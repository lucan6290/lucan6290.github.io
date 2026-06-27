from __future__ import annotations

from typing import Any

from ...core.response import fail, ok
from .registry import load_category_registry, save_category_registry, validate_category_registry


async def get_registry() -> dict[str, Any]:
    return ok(load_category_registry(include_compat=True))


async def update_registry(registry: list[dict[str, Any]]) -> dict[str, Any]:
    errors = validate_category_registry(registry)
    if errors:
        return fail("CATEGORY_REGISTRY_INVALID", "分类注册表校验失败", details={"validationErrors": errors})
    return ok(save_category_registry(registry))
