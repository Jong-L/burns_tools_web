"""种子数据：11 条认知扭曲选项的 code 注册（spec 1.2）+ 单用户锚点 jong(id=0)。

各语言的名称/默认描述在 backend/data/distortion_options_<lang>.json，
表里只存 code + sort_order（code 是唯一权威标识，文本不落库）。
"""

from __future__ import annotations

from sqlalchemy import engine, text

SINGLE_USER = {"id": 0, "username": "jong"}

# spec 1.2：sort_order 固定 1–11，顺序即列表枚举序
DISTORTION_CODES = [
    "all_or_nothing",
    "overgeneralization",
    "mental_filter",
    "disqualifying_the_positive",
    "mind_reading",
    "fortune_telling",
    "magnification_minimization",
    "emotional_reasoning",
    "should_statements",
    "labeling",
    "personalization",
]


def run(eng: engine.Engine) -> None:
    """幂等写入种子数据：单用户 + 11 条扭曲选项 code（已存在则跳过）。"""
    with eng.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (id, username) "
                "VALUES (:id, :username) "
                "ON CONFLICT(id) DO NOTHING"
            ),
            SINGLE_USER,
        )
        for i, code in enumerate(DISTORTION_CODES, start=1):
            conn.execute(
                text(
                    "INSERT INTO distortion_options (code, sort_order) "
                    "VALUES (:code, :sort_order) "
                    "ON CONFLICT(code) DO NOTHING"
                ),
                {"code": code, "sort_order": i},
            )
