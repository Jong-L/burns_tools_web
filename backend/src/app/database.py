"""数据库引擎、连接设置与会话管理。

SQLite 连接级 PRAGMA（spec 1.0）：
- foreign_keys = ON   外键与级联删除生效的前提
- busy_timeout = 5000 写锁竞争时等待 5s 再报错
- synchronous = NORMAL WAL 模式下安全且更快
库级 PRAGMA journal_mode = WAL 在 init_db() 时执行一次，持久生效。
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# backend/data/app.db —— 相对本文件向上两级（src/backend -> backend）
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{(DATA_DIR / 'app.db').as_posix()}"


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


engine = create_engine(
    DATABASE_URL,
    # FastAPI 每个请求一个线程，SQLite 必须允许跨线程复用连接
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _record):
    """每个新连接都设置连接级 PRAGMA（连接池里的新连接同样生效）。"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA busy_timeout = 5000")
    cursor.execute("PRAGMA synchronous = NORMAL")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    """FastAPI 依赖：每请求一个会话，用完关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """建表 + 种子数据。应用启动时调用一次（见 main.py）。"""
    # 导入 models 触发表定义注册，否则 create_all 无表可建
    from . import models, seed  # noqa: F401

    # 库级 PRAGMA：journal_mode 持久化在数据库文件里，执行一次即可
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode = WAL")
        conn.commit()

    Base.metadata.create_all(bind=engine)
    seed.run(engine)
