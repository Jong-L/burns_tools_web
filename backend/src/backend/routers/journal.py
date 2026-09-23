"""思维日志 API（spec 2.1）+ 认知扭曲选项接口（spec 2.6）。

单用户阶段：user_id 固定取服务端单用户 jong(id=0)，不从请求接收
（spec 1.0 越权防护：user_id 绝不允许来自请求体/查询串）。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from backend import models, schemas
from backend.database import get_db
from backend.seed import SINGLE_USER

router = APIRouter(prefix="/api", tags=["journal"])


def _current_user_id(db: Session) -> int:
    """现阶段单用户，直接取 jong(id=0)。将来接 JWT 后在这里解析会话。"""
    user = db.get(models.User, SINGLE_USER["id"])
    if user is None:
        raise HTTPException(status_code=500, detail="单用户种子数据缺失")
    return user.id


def _resolve_distortions(
    db: Session, items: list[schemas.DistortionIn]
) -> list[models.JournalDistortion]:
    """code 反查规范中文名写入 name 快照；非法 code / 重复 code 报 422。"""
    if not items:
        return []
    codes = [d.code for d in items]
    options = {
        o.code: o
        for o in db.scalars(
            select(models.DistortionOption).where(
                models.DistortionOption.code.in_(codes)
            )
        )
    }
    bad = [c for c in codes if c not in options]
    if bad:
        raise HTTPException(
            status_code=422,
            detail=f"未知的认知扭曲 code: {', '.join(sorted(set(bad)))}",
        )
    seen: set[str] = set()
    rows: list[models.JournalDistortion] = []
    for position, d in enumerate(items):
        if d.code in seen:
            raise HTTPException(
                status_code=422, detail=f"认知扭曲 code 重复: {d.code}"
            )
        seen.add(d.code)
        opt = options[d.code]
        rows.append(
            models.JournalDistortion(
                position=position,
                option_code=opt.code,
                name=opt.name_zh,
                note=d.note.strip(),
            )
        )
    return rows


def _get_log_or_404(db: Session, log_id: int, user_id: int) -> models.JournalLog:
    """按 id 取日志并校验归属（所有读写必须带 user_id，spec 3.9）。"""
    log = (
        db.execute(
            select(models.JournalLog)
            .options(joinedload(models.JournalLog.distortions))
            .where(models.JournalLog.id == log_id)
        )
        .unique()
        .scalar_one_or_none()
    )
    if log is None or log.user_id != user_id:
        # 不区分「不存在」与「不是你的」：不给外部探测空间
        raise HTTPException(status_code=404, detail="日志不存在")
    return log


@router.get("/journal/logs", response_model=list[schemas.JournalLogOut])
def list_logs(
    unanswered_first: bool = Query(
        False, description="true 时未回应（理性回应为空）的排最前"
    ),
    db: Session = Depends(get_db),
):
    """日志列表，组内按 timestamp 降序（越新越靠前）。"""
    user_id = _current_user_id(db)
    stmt = (
        select(models.JournalLog)
        .options(joinedload(models.JournalLog.distortions))
        .where(models.JournalLog.user_id == user_id)
    )
    if unanswered_first:
        stmt = stmt.order_by(
            (models.JournalLog.rational_response == "").desc(),
            models.JournalLog.timestamp.desc(),
        )
    else:
        stmt = stmt.order_by(models.JournalLog.timestamp.desc())
    return list(db.execute(stmt).unique().scalars())


@router.post(
    "/journal/logs", response_model=schemas.JournalLogOut, status_code=201
)
def create_log(
    payload: schemas.JournalLogCreate, db: Session = Depends(get_db)
):
    """新建日志 + distortions，同一事务写两张表（spec 1.0）。"""
    user_id = _current_user_id(db)
    if payload.type not in schemas.LOG_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"type 必须是 {' / '.join(schemas.LOG_TYPES)} 之一",
        )

    rows = _resolve_distortions(db, payload.distortions)
    log = models.JournalLog(
        user_id=user_id,
        type=payload.type,
        timestamp=payload.timestamp,  # 原值透传，不 round 不换算
        situation=payload.situation.strip(),
        emotion=payload.emotion.strip(),
        automatic_thought=payload.automatic_thought.strip(),
        rational_response=payload.rational_response.strip(),
        result=payload.result.strip(),
        distortions=rows,
    )
    db.add(log)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # (user_id, timestamp) UNIQUE 冲突：同一用户同一时间戳已存在
        raise HTTPException(
            status_code=409,
            detail="该时间戳已存在日志，请勿重复提交",
        )
    db.refresh(log)
    return log


@router.get("/journal/logs/{log_id}", response_model=schemas.JournalLogOut)
def get_log(log_id: int, db: Session = Depends(get_db)):
    user_id = _current_user_id(db)
    return _get_log_or_404(db, log_id, user_id)


@router.delete("/journal/logs/{log_id}", status_code=204)
def delete_log(log_id: int, db: Session = Depends(get_db)):
    user_id = _current_user_id(db)
    log = _get_log_or_404(db, log_id, user_id)
    db.delete(log)
    db.commit()


@router.put("/journal/logs/{log_id}", response_model=schemas.JournalLogOut)
def update_log(
    log_id: int,
    payload: schemas.JournalLogUpdate,
    db: Session = Depends(get_db),
):
    """部分更新：只处理客户端显式传来的字段；distortions 传入时整删重插。"""
    user_id = _current_user_id(db)
    log = _get_log_or_404(db, log_id, user_id)
    changes = payload.model_dump(exclude_unset=True)

    if "type" in changes and changes["type"] not in schemas.LOG_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"type 必须是 {' / '.join(schemas.LOG_TYPES)} 之一",
        )
    if changes.get("distortions") is not None:
        log.distortions = _resolve_distortions(
            db,
            [schemas.DistortionIn(**d) for d in changes.pop("distortions")],
        )

    for field, value in changes.items():
        # 文本字段按 spec 1.0 strip 后存 ''；timestamp 原值透传
        if isinstance(value, str):
            value = value.strip()
        setattr(log, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="该时间戳已存在其他日志"
        )
    db.refresh(log)
    return log


@router.get(
    "/distortion-options",
    response_model=list[schemas.DistortionOptionOut],
)
def list_distortion_options(db: Session = Depends(get_db)):
    """公开接口（spec 2.6）：11 项选项 + 中英默认描述，按 sort_order 升序。"""
    return list(
        db.scalars(
            select(models.DistortionOption).order_by(
                models.DistortionOption.sort_order.asc()
            )
        )
    )
