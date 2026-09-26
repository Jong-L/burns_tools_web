"""反驳"但是"法 API（spec 2.5 / 1.8）。

占位阶段：路由与 Pydantic 校验为真，返回固定示例数据；
存储层接入前不落库，仅用于联调前端交互逻辑。
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Path

from .. import schemas

router = APIRouter(prefix="/api", tags=["but_rebuttal"])

SAMPLE_DAY = "2026-09-24"


def _check_day(day: str) -> None:
    """day 格式校验：yyyy-MM-dd（spec 1.0）。非法格式 422。"""
    try:
        if date.fromisoformat(day).isoformat() != day:
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=422, detail="day 必须是 yyyy-MM-dd 格式")


# 示例数据：两轮已完成，验证链式解锁（第 3 行左列应解锁）与进度文案
_SAMPLE_ENTRIES_OUT = [
    schemas.ButRebuttalEntryOut(
        row_index=0, excuse_text="太累了，明天再做", rebuttal_text="只做 5 分钟，做完就可以停"
    ),
    schemas.ButRebuttalEntryOut(
        row_index=1, excuse_text="5 分钟也不够", rebuttal_text="5 分钟也比 0 分钟强"
    ),
]


@router.get(
    "/but-rebuttals/{day}",
    response_model=schemas.ButRebuttalDayOut,
)
def get_but_rebuttals(
    day: str = Path(description="yyyy-MM-dd"),
) -> schemas.ButRebuttalDayOut:
    """读某天的轮次列表，按 row_index 升序。占位：固定返回示例日（SAMPLE_DAY）的数据。"""
    _check_day(day)
    return schemas.ButRebuttalDayOut(day=SAMPLE_DAY, entries=_SAMPLE_ENTRIES_OUT)


@router.put(
    "/but-rebuttals/{day}",
    response_model=schemas.ButRebuttalDayOut,
)
def save_but_rebuttals(
    day: str,
    payload: schemas.ButRebuttalSaveIn,
) -> schemas.ButRebuttalDayOut:
    """覆盖保存某天（先删后插）。占位：校验后回显（row_index 按序重排）。"""
    _check_day(day)
    # spec 3.7 保存规则：两列全空的行丢弃；row_index 按保存顺序重排
    kept = [
        e for e in payload.entries
        if e.excuse_text.strip() or e.rebuttal_text.strip()
    ]
    entries = [
        schemas.ButRebuttalEntryOut(
            row_index=i,
            excuse_text=e.excuse_text.strip(),
            rebuttal_text=e.rebuttal_text.strip(),
        )
        for i, e in enumerate(kept)
    ]
    return schemas.ButRebuttalDayOut(day=day, entries=entries)
