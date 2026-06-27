from __future__ import annotations

from fastapi import APIRouter

from . import ai, article_index, assets, categories, content, gitops, health

router = APIRouter(prefix="/api/admin/v1")
router.include_router(health.router)
router.include_router(content.router)
router.include_router(categories.router)
router.include_router(assets.router)
router.include_router(ai.router)
router.include_router(article_index.router)
router.include_router(gitops.router)

