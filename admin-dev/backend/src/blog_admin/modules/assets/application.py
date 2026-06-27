from __future__ import annotations

from typing import Any

from fastapi.responses import FileResponse

from ...core.response import fail, ok
from ...core.settings import settings
from .schemas import AssetUsageRequest, UploadImageRequest
from .service import AssetService

asset_service = AssetService(settings.blog_root, settings.posts_dir)


async def create_folder(body: dict) -> Any:
    article_path = body.get("articlePath")
    if not article_path:
        return fail("VALIDATION_ERROR", "文章路径不能为空")
    return ok(asset_service.create_folder(article_path))


async def delete_folder(path: str) -> Any:
    return ok(asset_service.delete_folder(path))


async def upload_image(req: UploadImageRequest) -> Any:
    if not req.articlePath or not req.imageData or not req.extension:
        return fail("VALIDATION_ERROR", "缺少必要参数")
    return ok(asset_service.upload_image(req.articlePath, req.imageData, req.extension))


async def list_images(path: str) -> Any:
    return ok(asset_service.list_images(path))


async def get_image_folders() -> Any:
    return ok(asset_service.list_image_folders())


async def delete_image(path: str) -> Any:
    return ok(asset_service.delete_image(path))


async def get_unused_images(req: AssetUsageRequest) -> Any:
    return ok({"unusedImages": asset_service.list_unused_images(req.articlePath, req.content or "")})


async def cleanup_unused_images(req: AssetUsageRequest) -> Any:
    deleted = asset_service.delete_unused_images(req.articlePath, req.content or "")
    return ok({"deleted": deleted, "count": len(deleted)})


async def get_asset_file(path: str) -> Any:
    return FileResponse(asset_service.get_asset_file(path))
