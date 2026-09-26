"""思维日志 API（spec 2.1）+ 认知扭曲选项接口（spec 2.6）。

单用户阶段：user_id 固定取服务端单用户 jong(id=0)，不从请求接收
（spec 1.0 越权防护：user_id 绝不允许来自请求体/查询串）。
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from backend import models, schemas, text_data
from backend.database import get_db
from backend.seed import SINGLE_USER

router = APIRouter(prefix="/api", tags=["journal"])

DEFAULT_LANG = "zh"


def _lang_or_404(lang: str) -> str:
    """语言白名单校验：data 目录下实际存在 distortion_options_<lang>.json 才支持。"""
    if lang not in text_data.supported_languages("distortion_options"):
        raise HTTPException(status_code=404, detail=f"不支持的语言: {lang}")
    return lang


def _distortion_names(lang: str) -> dict[str, str]:
    """code -> 显示名 映射（按语言读 JSON，进程内缓存）。"""
    try:
        items = text_data.get_text_items("distortion_options", lang)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"数据文件缺失: {e.filename}")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"数据文件格式错误: {e}")
    return {item["code"]: item["name"] for item in items}


def _fill_distortion_names(
    log: models.JournalLog, names: dict[str, str]
) -> schemas.JournalLogOut:
    """ORM 日志 -> 输出模型，distortions 的 name 按 code 现查回填。

    不走 from_attributes 自动序列化：name 需要运行时按语言解析，
    手工构造以避免 ResponseValidationError（ORM 上没有 name 属性）。
    """
    return schemas.JournalLogOut(
        id=log.id,
        type=log.type,
        timestamp=log.timestamp,
        situation=log.situation,
        emotion=log.emotion,
        automatic_thought=log.automatic_thought,
        rational_response=log.rational_response,
        result=log.result,
        created_at=log.created_at,
        updated_at=log.updated_at,
        distortions=[
            schemas.DistortionOut(
                code=d.option_code,
                note=d.note,
                name=names.get(d.option_code or "", ""),
            )
            for d in log.distortions
        ],
    )


def _current_user_id(db: Session) -> int:
    """现阶段单用户，直接取 jong(id=0)。将来接 JWT 后在这里解析会话。"""
    user = db.get(models.User, SINGLE_USER["id"])
    if user is None:
        raise HTTPException(status_code=500, detail="单用户种子数据缺失")
    return user.id


def _resolve_distortions(
    db: Session, items: list[schemas.DistortionIn]
) -> list[models.JournalDistortion]:
    """写入路径只校验 code（合法 + 不重复，报 422）并落 option_code。

    name 快照已取消（spec 1.4 修订）：显示名读出时按 code + 语言现查，
    多语言界面下快照（冻结单一语言）与「跟随界面语言显示」互斥，取舍后者。
    """
    if not items:
        return []
    codes = [d.code for d in items]
    known = set(text_data.supported_languages("distortion_options")) and {
        item["code"]
        for lang in text_data.supported_languages("distortion_options")
        for item in text_data.load("distortion_options", lang)
    }
    bad = [c for c in codes if c not in known]
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
        rows.append(
            models.JournalDistortion(
                position=position,
                option_code=d.code,
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
    lang: str = Query(DEFAULT_LANG, description="扭曲显示名的语言"),
    db: Session = Depends(get_db),
):
    """日志列表，组内按 timestamp 降序（越新越靠前）。"""
    _lang_or_404(lang)
    names = _distortion_names(lang)
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
    logs = list(db.execute(stmt).unique().scalars())
    return [_fill_distortion_names(log, names) for log in logs]


@router.post(
    "/journal/logs", response_model=schemas.JournalLogOut, status_code=201
)
def create_log(
    payload: schemas.JournalLogCreate,
    lang: str = Query(DEFAULT_LANG, description="响应中扭曲显示名的语言"),
    db: Session = Depends(get_db),
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
    return _fill_distortion_names(log, _distortion_names(_lang_or_404(lang)))


@router.get("/journal/logs/{log_id}", response_model=schemas.JournalLogOut)
def get_log(
    log_id: int,
    lang: str = Query(DEFAULT_LANG, description="扭曲显示名的语言"),
    db: Session = Depends(get_db),
):
    _lang_or_404(lang)
    user_id = _current_user_id(db)
    log = _get_log_or_404(db, log_id, user_id)
    return _fill_distortion_names(log, _distortion_names(lang))


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
    lang: str = Query(DEFAULT_LANG, description="响应中扭曲显示名的语言"),
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
    return _fill_distortion_names(log, _distortion_names(_lang_or_404(lang)))


@router.get(
    "/distortion-options",
    response_model=list[schemas.DistortionOptionOut],
)
def list_distortion_options(
    lang: str = Query(DEFAULT_LANG, description="选项文本的语言"),
    db: Session = Depends(get_db),
):
    """公开接口（spec 2.6）：11 项选项 + 按语言的名称/默认描述，按 sort_order 升序。

    文本来自 backend/data/distortion_options_<lang>.json，表的 sort_order 定顺序。
    """
    _lang_or_404(lang)
    rows = db.scalars(
        select(models.DistortionOption).order_by(
            models.DistortionOption.sort_order.asc()
        )
    )
    items = {item["code"]: item for item in text_data.get_text_items("distortion_options", lang)}
    return [
        schemas.DistortionOptionOut(
            code=row.code,
            name=items[row.code]["name"],
            default_note=items[row.code]["default_note"],
        )
        for row in rows
    ]
