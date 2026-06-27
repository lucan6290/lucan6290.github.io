from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body

from blog_admin.modules.categories import application

router = APIRouter(prefix="/categories", tags=["分类管理"])


@router.get("/registry")
async def get_registry():
    return await application.get_registry()


@router.put("/registry")
async def update_registry(registry: list[dict[str, Any]] = Body(...)):
    return await application.update_registry(registry)

