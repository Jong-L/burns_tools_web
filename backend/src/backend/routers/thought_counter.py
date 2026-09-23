"""消极思维计数器 API（spec 2.2）。

占位阶段：路由与 Pydantic 校验为真，返回固定示例数据；
存储层接入前不落库，仅用于联调前端交互逻辑。

统计图的日序列是纯前端计算（spec 2.2），因此只需要这一个读接口。
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Path

from backend import schemas

router = APIRouter(prefix="/api", tags=["thought_counter"])


def _check_day(day: str) -> None:
    """day 格式校验：yyyy-MM-dd（spec 1.0）。非法格式 422。"""
    try:
        if date.fromisoformat(day).isoformat() != day:
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=422, detail="day 必须是 yyyy-MM-dd 格式")


# 示例数据：前端统计图 / 列表渲染可先基于它开发
_SAMPLE_COUNTS: list[schemas.ThoughtCountOut] = [
    schemas.ThoughtCountOut(day="2026-09-20", count=5),
    schemas.ThoughtCountOut(day="2026-09-22", count=3),
    schemas.ThoughtCountOut(day="2026-09-24", count=1),
]


@router.get("/thought-counts", response_model=list[schemas.ThoughtCountOut])
def list_thought_counts() -> list[schemas.ThoughtCountOut]:
    """全部天的计数，按 day 升序（spec 2.2）。占位：返回示例数据。"""
    return _SAMPLE_COUNTS


@router.put("/thought-counts/{day}", response_model=schemas.ThoughtCountOut)
def save_thought_count(
    payload: schemas.ThoughtCountIn,
    day: str = Path(description="yyyy-MM-dd"),
) -> schemas.ThoughtCountOut:
    """覆盖保存某天的计数（upsert，非累加，spec 3.5）。占位：只做校验与回显。"""
    _check_day(day)
    return schemas.ThoughtCountOut(day=day, count=payload.count)
