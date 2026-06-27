"""Post read/write adapters used by AI workflows."""
from __future__ import annotations

import re
from typing import Any

from ...core.response import fail
from ...core.schemas import CreatePostRequest, UpdatePostRequest
from ...core.settings import settings
from ..categories.registry import find_secondary_by_prefix
from .schemas import AIDraftPlan


def _body_from_raw(raw: str) -> str:
    if not raw.startswith("---"):
        return raw
    match = re.match(r"^---\s*\n.*?\n---\s*\n?(.*)$", raw, re.S)
    return match.group(1) if match else raw


def _error_message(result: dict[str, Any], default: str) -> str:
    error = result.get("error")
    if isinstance(error, dict):
        return str(error.get("message") or error.get("code") or default)
    return str(error or default)


async def create_post_file(title: str, prefix1: str, prefix2: str) -> dict[str, Any]:
    from ..content import application as content_application

    result = await content_application.create_post(
        CreatePostRequest(title=title, prefix1=prefix1, prefix2=prefix2)
    )
    if not isinstance(result, dict):
        return fail("POST_CREATE_FAILED", "创建文章失败")
    return result


async def update_post_file(path: str, front_matter_patch: dict[str, Any] | None, content: str | None) -> dict[str, Any]:
    from ..content import application as content_application

    result = await content_application.update_post(
        path,
        UpdatePostRequest(frontMatter=front_matter_patch, content=content),
    )
    if not isinstance(result, dict):
        return fail("POST_WRITE_FAILED", "保存文章失败")
    return result


async def read_post(path: str) -> tuple[str, dict[str, Any], str, str] | None:
    from ..content import application as content_application

    result = await content_application.get_post(path)
    if not isinstance(result, dict) or not result.get("success"):
        return None
    data = result.get("data") or {}
    raw = str(data.get("raw") or data.get("content") or "")
    raw_front_matter = data.get("frontMatter")
    front_matter: dict[str, Any] = raw_front_matter if isinstance(raw_front_matter, dict) else {}
    body = _body_from_raw(raw)
    return path, front_matter, body, raw


def frontmatter_for_plan(plan: AIDraftPlan) -> dict[str, Any]:
    registry_item = find_secondary_by_prefix(plan.prefix1, plan.prefix2)
    if registry_item:
        primary, secondary = registry_item
        primary_name = primary["frontend_name1"]
        secondary_name = secondary["frontend_name2"]
        cover = primary.get("cover")
    else:
        primary_name = plan.primaryName
        secondary_name = plan.prefix2
        cover = settings.prefix_to_dir.get(plan.prefix1, {}).get("cover")
    return {
        "title": plan.title,
        "categories": [[primary_name, secondary_name]],
        "tags": plan.tags,
        "description": plan.description,
        "layout": "post",
        "comments": True,
        "published": True,
        "lang": "zh-CN",
        "cover": cover,
        "status": "draft",
    }


def response_error(result: dict[str, Any], default: str) -> str:
    return _error_message(result, default)
