from __future__ import annotations

from fastapi import APIRouter

from ....core.response import ok

router = APIRouter(tags=["健康检查"])


@router.get("/health")
async def health():
    return ok({"status": "ok"})

