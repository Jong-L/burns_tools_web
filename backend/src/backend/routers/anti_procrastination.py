"""反拖延症表 API（spec 2.4 / 1.7）。

占位阶段：路由与 Pydantic 校验为真，返回固定示例数据；
存储层接入前不落库，仅用于联调前端交互逻辑。
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Path

from backend import schemas

router = APIRouter(prefix="/api", tags=["anti_procrastination"])

SAMPLE_DAY = "2026-09-24"


def _check_day(day: str) -> None:
    """day 格式校验：yyyy-MM-dd（spec 1.0）。非法格式 422。"""
    try:
        if date.fromisoformat(day).isoformat() != day:
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=422, detail="day 必须是 yyyy-MM-dd 格式")


def _with_row_index(
    entries: list[schemas.AntiProcrastinationEntryIn],
) -> list[schemas.AntiProcrastinationEntryOut]:
    """row_index 由服务端按数组序赋值（spec 2.4，客户端不传）。"""
    return [
        schemas.AntiProcrastinationEntryOut(
            row_index=i,
            activity=e.activity.strip(),
            predicted_difficulty=e.predicted_difficulty,
            predicted_satisfaction=e.predicted_satisfaction,
            actual_difficulty=e.actual_difficulty,
            actual_satisfaction=e.actual_satisfaction,
        )
        for i, e in enumerate(entries)
    ]


# 示例数据：半填充状态，含分数齐全行与只填活动名的行
_SAMPLE_ENTRIES_OUT = [
    schemas.AntiProcrastinationEntryOut(
        row_index=0, activity="写周报",
        predicted_difficulty=80, predicted_satisfaction=60,
        actual_difficulty=50, actual_satisfaction=75,
    ),
    schemas.AntiProcrastinationEntryOut(
        row_index=1, activity="整理书桌",
        predicted_difficulty=None, predicted_satisfaction=None,
        actual_difficulty=None, actual_satisfaction=None,
    ),
]


@router.get(
    "/anti-procrastination/{day}",
    response_model=schemas.AntiProcrastinationDayOut,
)
def get_anti_procrastination(
    day: str = Path(description="yyyy-MM-dd"),
) -> schemas.AntiProcrastinationDayOut:
    """读某天的行列表，按 row_index 升序。占位：固定返回示例日（SAMPLE_DAY）的数据。"""
    _check_day(day)
    return schemas.AntiProcrastinationDayOut(day=SAMPLE_DAY, entries=_SAMPLE_ENTRIES_OUT)


@router.put(
    "/anti-procrastination/{day}",
    response_model=schemas.AntiProcrastinationDayOut,
)
def save_anti_procrastination(
    day: str,
    payload: schemas.AntiProcrastinationSaveIn,
) -> schemas.AntiProcrastinationDayOut:
    """覆盖保存某天（先删后插）。占位：校验后回显（row_index 按序重排）。"""
    _check_day(day)
    # spec 3.4 整行丢弃规则：活动名与四个百分比全空的行不落库
    kept = [
        e for e in payload.entries
        if e.activity.strip()
        or any(
            v is not None
            for v in (
                e.predicted_difficulty, e.predicted_satisfaction,
                e.actual_difficulty, e.actual_satisfaction,
            )
        )
    ]
    return schemas.AntiProcrastinationDayOut(
        day=day, entries=_with_row_index(kept)
    )
