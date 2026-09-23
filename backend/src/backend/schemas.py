"""Pydantic 请求/响应模型。

对应 spec 2.1（思维日志）与 2.6（扭曲选项）的 API 边界。
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

LOG_TYPES = ("three_column", "six_column")


class DistortionIn(BaseModel):
    """写入用：扭曲只传 code + 用户描述，name 由服务端反查快照（spec 2.1）。"""

    code: str = Field(min_length=1)
    note: str = ""


class JournalLogCreate(BaseModel):
    type: str = "three_column"
    timestamp: float = Field(..., description="Unix 秒级时间戳，原值透传")
    situation: str = ""
    emotion: str = ""
    automatic_thought: str = ""
    rational_response: str = ""
    result: str = ""
    distortions: list[DistortionIn] = []

    @field_validator("type", mode="before")
    @classmethod
    def blank_type_defaults(cls, v):
        """spec 1.3：type 写入时空白兜底 three_column。"""
        if v is None or (isinstance(v, str) and not v.strip()):
            return "three_column"
        return v


class JournalLogUpdate(BaseModel):
    """PUT 全部字段可选：只更新客户端明确传来的字段（用 exclude_unset 区分）。"""

    type: str | None = None
    timestamp: float | None = None
    situation: str | None = None
    emotion: str | None = None
    automatic_thought: str | None = None
    rational_response: str | None = None
    result: str | None = None
    distortions: list[DistortionIn] | None = None

    @field_validator("type")
    @classmethod
    def type_in_enum(cls, v):
        if v is not None and v not in LOG_TYPES:
            raise ValueError(f"type 必须是 {' / '.join(LOG_TYPES)} 之一")
        return v


class DistortionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    # ORM 列名是 option_code，对外统一叫 code（spec 2.1 读出形态）
    code: str | None = Field(validation_alias="option_code")
    name: str
    note: str


class JournalLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    timestamp: float
    situation: str
    emotion: str
    automatic_thought: str
    rational_response: str
    result: str
    created_at: datetime
    updated_at: datetime
    distortions: list[DistortionOut]


class DistortionOptionOut(BaseModel):
    """GET /api/distortion-options：中英双语选项 + 默认描述（spec 2.6）。"""

    model_config = ConfigDict(from_attributes=True)

    code: str
    name_zh: str
    name_en: str
    default_note_zh: str
    default_note_en: str


class ToolOut(BaseModel):
    """GET /api/tools：工具列表项（静态数据，见 routers/tools.py）。"""

    id: str
    name: str
    description: str


# ---- 其余 4 个工具的 API 契约模型 ----
# 占位阶段：路由与校验为真，存储逻辑待接入（返回示例数据）。
# GET / PUT 同构返回「某天的完整状态」，前端保存后可直接更新 state。

class ThoughtCountOut(BaseModel):
    """GET /api/thought-counts 列表项。"""

    day: str
    count: int


class ThoughtCountIn(BaseModel):
    """PUT /api/thought-counts/{day} 请求体。"""

    count: int = Field(ge=0, description="当天计数，非负整数")


class DailyPlanEntryIn(BaseModel):
    """PUT /api/daily-plans/{day} 的单槽位写入（time_slot 服务端派生，不收）。"""

    slot_index: int = Field(ge=0, le=13)
    plan: str = ""
    actual: str = ""
    mastery_score: int | None = Field(None, ge=0, le=5)
    pleasure_score: int | None = Field(None, ge=0, le=5)


class DailyPlanEntryOut(BaseModel):
    slot_index: int
    time_slot: str
    plan: str
    actual: str
    mastery_score: int | None = None
    pleasure_score: int | None = None


class DailyPlanDayOut(BaseModel):
    """某天的完整 14 槽位状态（缺的槽位补空行）。"""

    day: str
    entries: list[DailyPlanEntryOut]


class DailyPlanSaveIn(BaseModel):
    entries: list[DailyPlanEntryIn] = []


class AntiProcrastinationEntryIn(BaseModel):
    """PUT /api/anti-procrastination/{day} 的单行写入（row_index 服务端按序赋值）。"""

    activity: str = ""
    predicted_difficulty: int | None = Field(None, ge=0, le=100)
    predicted_satisfaction: int | None = Field(None, ge=0, le=100)
    actual_difficulty: int | None = Field(None, ge=0, le=100)
    actual_satisfaction: int | None = Field(None, ge=0, le=100)


class AntiProcrastinationEntryOut(BaseModel):
    row_index: int
    activity: str
    predicted_difficulty: int | None = None
    predicted_satisfaction: int | None = None
    actual_difficulty: int | None = None
    actual_satisfaction: int | None = None


class AntiProcrastinationDayOut(BaseModel):
    day: str
    entries: list[AntiProcrastinationEntryOut]


class AntiProcrastinationSaveIn(BaseModel):
    entries: list[AntiProcrastinationEntryIn] = []


class ButRebuttalEntryIn(BaseModel):
    """PUT /api/but-rebuttals/{day} 的单行写入。"""

    excuse_text: str = ""
    rebuttal_text: str = ""


class ButRebuttalEntryOut(BaseModel):
    row_index: int
    excuse_text: str
    rebuttal_text: str


class ButRebuttalDayOut(BaseModel):
    day: str
    entries: list[ButRebuttalEntryOut]


class ButRebuttalSaveIn(BaseModel):
    entries: list[ButRebuttalEntryIn] = []
