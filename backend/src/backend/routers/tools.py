"""工具列表 API：5 个心理自助工具的 id/名称/描述。

数据文件 backend/data/tools.json（内容来自老项目 burns_tools/data/tools.json）。
spec 的 8 张业务表里没有工具表，工具清单是静态数据，不走数据库；
后续新工具上线时在 tools.json 里加一项即可。
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend import schemas

DATA_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "tools.json"

router = APIRouter(prefix="/api", tags=["tools"])


@lru_cache
def _load_tools() -> tuple[schemas.ToolOut, ...]:
    """读 tools.json 并做 Pydantic 校验；进程内缓存，改文件需重启（dev 用 --reload 会自动重载）。"""
    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"数据文件缺失: {DATA_FILE}")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"数据文件格式错误: {e}")
    return tuple(schemas.ToolOut(**item) for item in raw["tools"])


@router.get("/tools", response_model=list[schemas.ToolOut])
def list_tools() -> list[schemas.ToolOut]:
    return list(_load_tools())
