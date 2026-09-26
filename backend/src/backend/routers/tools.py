"""工具列表 API：5 个心理自助工具的 id/名称/描述，按语言返回。

文案数据 backend/data/tools_<lang>.json（zh / en），由 text_data 加载；
spec 的 8 张业务表里没有工具表，工具清单是静态数据，不走数据库；
后续新工具上线时在各语言文件里加一项即可。
"""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from backend import schemas, text_data

router = APIRouter(prefix="/api", tags=["tools"])


@router.get("/tools", response_model=list[schemas.ToolOut])
def list_tools(lang: str = "zh") -> list[schemas.ToolOut]:
    try:
        items = text_data.get_text_items("tools", lang)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"不支持的语言: {lang}")
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"数据文件缺失: {e.filename}")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"数据文件格式错误: {e}")
    return [schemas.ToolOut(**item) for item in items]
