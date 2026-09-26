"""按语言加载 backend/data 下的静态文本数据（tools / distortion_options）。

文件约定：<name>_<lang>.json，白名单 = 磁盘上实际存在的语言文件——
磁盘上有哪种语言，API 就承诺支持哪种；请求未支持的语言由调用方 404。
进程内缓存；dev 用 uvicorn --reload 时改文件自动重载。
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

# routers/ 的上级的上级的上级 = 项目 backend/ 目录
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def supported_languages(name: str) -> tuple[str, ...]:
    """某类数据当前支持的语言列表（扫描 <name>_<lang>.json）。"""
    return tuple(sorted(p.stem.removeprefix(f"{name}_") for p in DATA_DIR.glob(f"{name}_*.json")))


@lru_cache(maxsize=None)
def load(name: str, lang: str) -> tuple[dict, ...]:
    """读 <name>_<lang>.json 并返回条目元组；文件缺失/格式错报 FileNotFoundError/JSONDecodeError。"""
    data_file = DATA_DIR / f"{name}_{lang}.json"
    raw = json.loads(data_file.read_text(encoding="utf-8"))
    # 每类文件的条目都包在唯一的顶层键里（tools / options）
    (items,) = raw.values()
    return tuple(items)


def get_text_items(name: str, lang: str) -> tuple[dict, ...]:
    """带白名单校验的读取入口：语言不支持抛 KeyError，路由层转 404。"""
    if lang not in supported_languages(name):
        raise KeyError(lang)
    return load(name, lang)
