from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from ...core.response import fail, ok
from ...core.settings import settings
from ..assets.service import AssetService
from .frontmatter import generate_frontmatter, parse_frontmatter
from .index_sync import PostIndexSyncService
from .infrastructure import HexoPostCreator
from .repository import PostRepository
from .schemas import CreatePostRequest, UpdatePostRequest

post_repository = PostRepository()
post_index_sync = PostIndexSyncService(repository=post_repository)
asset_service = AssetService(settings.blog_root, settings.posts_dir)


def _create_post_file(title: str, prefix1: str, prefix2: str) -> dict[str, Any]:
    return HexoPostCreator().create(title, prefix1, prefix2)


async def list_posts() -> dict[str, Any]:
    try:
        posts = []
        for file_path in post_repository.list_markdown_files():
            post = post_repository.parse_post_summary(file_path)
            if post:
                posts.append(post)
        posts.sort(key=lambda item: item.get("date", ""), reverse=True)
        return ok(posts)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取文章列表失败: {exc}") from exc


async def get_post(path: str) -> dict[str, Any]:
    if not post_repository.exists(path):
        return fail("POST_NOT_FOUND", "文章不存在")

    try:
        content = post_repository.read_raw(path)
        front_matter, _ = parse_frontmatter(content)
        return ok(
            {
                "frontMatter": front_matter,
                "content": content,
                "raw": content,
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"读取文章失败: {exc}") from exc


async def create_post(req: CreatePostRequest) -> dict[str, Any]:
    return _create_post_file(req.title, req.prefix1, req.prefix2)


async def update_post(path: str, req: UpdatePostRequest) -> dict[str, Any]:
    if not post_repository.exists(path):
        return fail("POST_NOT_FOUND", "文章不存在")

    try:
        existing = post_repository.read_raw(path)
        existing_fm, _ = parse_frontmatter(existing)
        next_fm = dict(existing_fm)
        if req.frontMatter:
            next_fm.update(req.frontMatter)
        next_fm["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_content = generate_frontmatter(next_fm) + (req.content or "")
        post_repository.write_raw(path, new_content)

        post_index_sync.sync_on_update(
            existing_fm=existing_fm,
            new_fm=next_fm,
            filename=Path(path).stem,
        )

        return ok(
            {
                "path": path,
                "unusedImages": asset_service.list_unused_images(path, new_content),
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"更新文章失败: {exc}") from exc


async def delete_post(path: str) -> dict[str, Any]:
    if not post_repository.exists(path):
        return fail("POST_NOT_FOUND", "文章不存在")

    try:
        filename = Path(path).stem
        post_index_sync.remove_post(filename)
        post_repository.delete(path)
        return ok({"path": path})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"删除文章失败: {exc}") from exc
