from __future__ import annotations

from fastapi import APIRouter

from blog_admin.modules.content import application
from blog_admin.modules.content.schemas import CreatePostRequest, UpdatePostRequest

router = APIRouter(prefix="/posts", tags=["文章管理"])


@router.get("")
async def list_posts():
    return await application.list_posts()


@router.post("")
async def create_post(req: CreatePostRequest):
    return await application.create_post(req)


@router.get("/{path:path}")
async def get_post(path: str):
    return await application.get_post(path)


@router.put("/{path:path}")
async def update_post(path: str, req: UpdatePostRequest):
    return await application.update_post(path, req)


@router.delete("/{path:path}")
async def delete_post(path: str):
    return await application.delete_post(path)
