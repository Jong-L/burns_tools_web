"""ORM 模型：spec 1.1 / 1.2 / 1.3 / 1.4 四张表。

字段与 docs/data-layer-spec.md 逐条对应；约束分层约定（spec 1.0）：
API 层（Pydantic + 路由）负责可读报错，数据库 CHECK 只做兜底。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class User(Base):
    """users —— 鉴权锚点表（spec 1.1）。现阶段单用户 jong(id=0)。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class DistortionOption(Base):
    """distortion_options —— 认知扭曲参考表（spec 1.2），11 条种子数据。"""

    __tablename__ = "distortion_options"

    code = mapped_column(String, primary_key=True)
    name_zh: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[str] = mapped_column(Text, nullable=False)
    default_note_zh: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=""
    )
    default_note_en: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=""
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)


class JournalLog(Base):
    """journal_logs —— 思维日志主表（spec 1.3）。"""

    __tablename__ = "journal_logs"
    __table_args__ = (
        CheckConstraint("type IN ('three_column', 'six_column')", name="ck_type"),
        UniqueConstraint("user_id", "timestamp", name="uq_user_timestamp"),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(Text, nullable=False)
    # 业务时间戳：秒，可含小数，原值透传（spec 1.3 硬性约定）
    timestamp: Mapped[float] = mapped_column(Float, nullable=False)
    situation: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    emotion: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    automatic_thought: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=""
    )
    rational_response: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=""
    )
    result: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    distortions: Mapped[list["JournalDistortion"]] = relationship(
        back_populates="log",
        cascade="all, delete-orphan",
        order_by="JournalDistortion.position",
        # 级联删除由数据库外键 ON DELETE CASCADE 与 ORM cascade 双保险
        passive_deletes=True,
    )


class JournalDistortion(Base):
    """journal_distortions —— 认知扭曲子表（spec 1.4），1 对多挂主表。"""

    __tablename__ = "journal_distortions"
    __table_args__ = (CheckConstraint("position >= 0", name="ck_position"),)

    log_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("journal_logs.id", ondelete="CASCADE"),
        primary_key=True,
    )
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    option_code: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("distortion_options.code"),
        nullable=True,
    )
    # 快照：写入时由服务端按 code 反查规范中文名（spec 1.4）
    name: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False, server_default="")

    log: Mapped[JournalLog] = relationship(back_populates="distortions")
