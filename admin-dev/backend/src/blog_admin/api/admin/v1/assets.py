from __future__ import annotations

from fastapi import APIRouter

from blog_admin.modules.assets import application
from blog_admin.modules.assets.schemas import AssetUsageRequest, UploadImageRequest

router = APIRouter(prefix="/assets", tags=["资源管理"])


@router.post("/folders")
async def create_folder(body: dict):
    return await application.create_folder(body)


@router.delete("/folders/{path:path}")
async def delete_folder(path: str):
    return await application.delete_folder(path)


@router.post("/images")
async def upload_image(req: UploadImageRequest):
    return await application.upload_image(req)


@router.get("/images/{article_path:path}")
async def list_images(article_path: str):
    return await application.list_images(article_path)


@router.delete("/images/{path:path}")
async def delete_image(path: str):
    return await application.delete_image(path)


@router.get("/folders")
async def get_image_folders():
    return await application.get_image_folders()


@router.post("/unused")
async def get_unused_images(req: AssetUsageRequest):
    return await application.get_unused_images(req)


@router.post("/cleanup-unused")
async def cleanup_unused_images(req: AssetUsageRequest):
    return await application.cleanup_unused_images(req)


@router.get("/file/{path:path}")
async def get_asset_file(path: str):
    return await application.get_asset_file(path)
