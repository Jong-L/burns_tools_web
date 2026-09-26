"""每日活动计划表 API（spec 2.3 / 1.6）。

占位阶段：路由与 Pydantic 校验为真，返回固定示例数据；
存储层接入前不落库，仅用于联调前端交互逻辑。
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Path

from .. import schemas

router = APIRouter(prefix="/api", tags=["daily_plan"])

# 权威清单（spec 1.6 表）：slot_index → 规范文案，写入/读出均由此派生
TIME_SLOTS = [
    "上午 8-9", "上午 9-10", "上午 10-11", "上午 11-12",
    "下午 12-1", "下午 1-2", "下午 2-3", "下午 3-4",
    "下午 4-5", "下午 5-6", "下午 6-7", "晚上 7-8",
    "晚上 8-9", "晚上 9-12",
]

SAMPLE_DAY = "2026-09-24"


def _check_day(day: str) -> None:
    """day 格式校验：yyyy-MM-dd（spec 1.0）。非法格式 422。"""
    try:
        if date.fromisoformat(day).isoformat() != day:
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=422, detail="day 必须是 yyyy-MM-dd 格式")


def _full_day(entries: list[schemas.DailyPlanEntryOut]) -> schemas.DailyPlanDayOut:
    """补齐 14 个槽位：缺的槽位补空行（spec 2.3 读库回填规则）。"""
    by_index = {e.slot_index: e for e in entries}
    return schemas.DailyPlanDayOut(
        day=SAMPLE_DAY,
        entries=[
            by_index.get(
                i,
                schemas.DailyPlanEntryOut(
                    slot_index=i, time_slot=TIME_SLOTS[i],
                    plan="", actual="", mastery_score=None, pleasure_score=None,
                ),
            )
            for i in range(14)
        ],
    )


# 示例数据：半填充状态（前 2 个槽位有内容），空态/填充态前端都能验
_SAMPLE_ENTRIES = [
    schemas.DailyPlanEntryOut(
        slot_index=0, time_slot=TIME_SLOTS[0], plan="晨跑 30 分钟",
        actual="跑了 20 分钟", mastery_score=3, pleasure_score=4,
    ),
    schemas.DailyPlanEntryOut(
        slot_index=4, time_slot=TIME_SLOTS[4], plan="读《伯恩斯新情绪疗法》一章",
        actual="", mastery_score=2, pleasure_score=None,
    ),
]


@router.get("/daily-plans/{day}", response_model=schemas.DailyPlanDayOut)
def get_daily_plan(day: str = Path(description="yyyy-MM-dd")) -> schemas.DailyPlanDayOut:
    """读某天的 14 槽位完整状态。占位：固定返回示例日（SAMPLE_DAY）的数据。"""
    _check_day(day)
    return _full_day(_SAMPLE_ENTRIES)


@router.put("/daily-plans/{day}", response_model=schemas.DailyPlanDayOut)
def save_daily_plan(
    day: str,
    payload: schemas.DailyPlanSaveIn,
) -> schemas.DailyPlanDayOut:
    """覆盖保存某天（先删后插，spec 1.0 事务）。占位：校验后按保存内容回显完整 14 槽位。"""
    _check_day(day)
    saved = [
        schemas.DailyPlanEntryOut(
            slot_index=e.slot_index,
            time_slot=TIME_SLOTS[e.slot_index],  # 规范文案由服务端派生，不采信客户端
            plan=e.plan.strip(),
            actual=e.actual.strip(),
            mastery_score=e.mastery_score,
            pleasure_score=e.pleasure_score,
        )
        for e in payload.entries[:14]  # spec 1.6：超出 14 槽位截断
    ]
    out = _full_day(saved)
    out.day = day  # 回显客户端请求的 day（真实现阶段存的就是它）
    return out
