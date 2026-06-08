"""
Git 平台配置路由
GET/POST /api/git-config
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter

from ..config import BLOG_ROOT

router = APIRouter(prefix="/api/git-config", tags=["Git 平台配置"])

# 配置文件路径（统一使用 admin-dev/.env，.env.development 为模板文件）
ADMIN_DEV_DIR = Path(__file__).resolve().parent.parent.parent.parent  # blog/admin-dev/
ENV_FILE = ADMIN_DEV_DIR / ".env"
HISTORY_FILE = ADMIN_DEV_DIR / "git-platform-history.json"

PLATFORMS = ["github", "gitee"]
FIELDS = ["token", "owner", "repo", "branch"]

# .env 字段名映射
ENV_KEYS = {
    f"{p}_{f}": f"{p.upper()}_{f.upper()}"
    for p in PLATFORMS
    for f in FIELDS
}


def _read_env() -> Dict[str, str]:
    """读取 .env 文件为字典"""
    result = {}
    if not ENV_FILE.exists():
        return result
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
    return result


def _write_env(data: Dict[str, str]) -> None:
    """写入 .env 文件，保留非 Git 平台的其他配置"""
    # 先读取已有内容，保留非 GITHUB/GITEE 开头的行
    preserved_lines: List[str] = []
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                key = stripped.split("=", 1)[0].strip()
                if not key.startswith(("GITHUB_", "GITEE_")):
                    preserved_lines.append(line)
            elif stripped.startswith("#") and not any(
                stripped.upper().startswith(f"# {p}") for p in PLATFORMS
            ):
                preserved_lines.append(line)

    lines = list(preserved_lines)
    if lines and lines[-1] != "":
        lines.append("")
    lines.append("# Git 平台配置")
    lines.append("")
    for platform in PLATFORMS:
        lines.append(f"# {platform.upper()}")
        for field in FIELDS:
            key = f"{platform.upper()}_{field.upper()}"
            value = data.get(key, "")
            lines.append(f"{key}={value}")
        lines.append("")
    ENV_FILE.write_text("\n".join(lines), encoding="utf-8")


def _read_history() -> Dict[str, Dict[str, List[str]]]:
    """读取历史记录"""
    if not HISTORY_FILE.exists():
        return {p: {f: [] for f in FIELDS} for p in PLATFORMS}
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {p: {f: [] for f in FIELDS} for p in PLATFORMS}


def _write_history(history: Dict[str, Dict[str, List[str]]]) -> None:
    """写入历史记录"""
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def _update_history(history: Dict[str, Dict[str, List[str]]], platform: str, field: str, value: str) -> None:
    """向历史记录中添加值（去重，最新值排最前），Token 不记录"""
    if not value or field == "token":
        return
    lst = history.get(platform, {}).get(field, [])
    if value in lst:
        lst.remove(value)
    lst.insert(0, value)
    # 每个字段最多保留 10 条历史
    history.setdefault(platform, {})[field] = lst[:10]


@router.get("")
async def get_git_config():
    """获取 Git 平台配置 + 历史选项"""
    env = _read_env()
    history = _read_history()

    config: Dict[str, Dict[str, str]] = {}
    options: Dict[str, Dict[str, List[Dict[str, str]]]] = {}

    for platform in PLATFORMS:
        config[platform] = {}
        options[platform] = {}
        for field in FIELDS:
            key = f"{platform.upper()}_{field.upper()}"
            config[platform][field] = env.get(key, "")
            hist = history.get(platform, {}).get(field, [])
            options[platform][field] = [{"label": v, "value": v} for v in hist]

    return {"success": True, "data": {"config": config, "options": options}}


@router.post("")
async def save_git_config(payload: Dict[str, Any]):
    """保存 Git 平台配置"""
    env = _read_env()
    history = _read_history()

    for platform in PLATFORMS:
        platform_data = payload.get(platform, {})
        for field in FIELDS:
            value = platform_data.get(field, "")
            key = f"{platform.upper()}_{field.upper()}"
            env[key] = value
            _update_history(history, platform, field, value)

    _write_env(env)
    _write_history(history)

    return {"success": True, "data": None}


@router.delete("/history/{platform}/{field}/{value:path}")
async def delete_history_item(platform: str, field: str, value: str):
    """删除某条历史记录"""
    history = _read_history()
    lst = history.get(platform, {}).get(field, [])
    if value in lst:
        lst.remove(value)
        history.setdefault(platform, {})[field] = lst
        _write_history(history)
    return {"success": True}
