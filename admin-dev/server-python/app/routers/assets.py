"""
图片管理路由
POST/GET/DELETE /api/assets/*
"""
from __future__ import annotations

import base64
import re
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException

from ..config import BLOG_ROOT, POSTS_DIR
from ..schemas import ApiResponse, ImageInfo, UploadImageRequest
from ..services.frontmatter import get_asset_folder_path, get_next_image_number

router = APIRouter(prefix="/api/assets", tags=["资源管理"])


# ============================================================
# 资源文件夹管理
# ============================================================

@router.post("/folder")
async def create_folder(body: dict):
    """创建资源文件夹"""
    article_path = body.get("articlePath")
    if not article_path:
        return ApiResponse(success=False, error="文章路径不能为空")

    asset_folder = get_asset_folder_path(article_path, POSTS_DIR)
    if asset_folder.exists():
        return ApiResponse(success=False, error="资源文件夹已存在")

    asset_folder.mkdir(parents=True, exist_ok=True)
    relative = asset_folder.relative_to(POSTS_DIR).as_posix()
    return ApiResponse(success=True, data={"path": relative})


@router.delete("/folder/{path:path}")
async def delete_folder(path: str):
    """删除资源文件夹"""
    full_path = POSTS_DIR / path
    if not full_path.exists():
        return ApiResponse(success=False, error="资源文件夹不存在")

    shutil.rmtree(full_path, ignore_errors=True)
    return ApiResponse(success=True, data={"path": path})


# ============================================================
# 图片管理
# ============================================================

@router.post("/image")
async def upload_image(req: UploadImageRequest):
    """上传图片到文章资源文件夹"""
    if not req.articlePath or not req.imageData or not req.extension:
        return ApiResponse(success=False, error="缺少必要参数")

    try:
        asset_folder = get_asset_folder_path(req.articlePath, POSTS_DIR)
        asset_folder.mkdir(parents=True, exist_ok=True)

        # 获取下一个图片编号
        next_num = get_next_image_number(req.articlePath, POSTS_DIR)

        # 文章名（不含扩展名）
        article_name = Path(req.articlePath).stem

        # 生成图片文件名
        image_name = f"{article_name}-img{next_num}.{req.extension}"
        image_path = asset_folder / image_name

        # 解码 Base64 数据（去除 data:image/xxx;base64, 前缀）
        b64_data = re.sub(r"^data:image/\w+;base64,", "", req.imageData)
        image_bytes = base64.b64decode(b64_data)

        image_path.write_bytes(image_bytes)

        relative = image_path.relative_to(POSTS_DIR).as_posix()
        url = "/" + image_path.relative_to(BLOG_ROOT).as_posix()

        return ApiResponse(success=True, data=ImageInfo(
            name=image_name,
            path=relative,
            url=url,
        ).model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传图片失败: {e}")


@router.get("/images/{path:path}")
async def list_images(path: str):
    """获取文章的所有图片"""
    asset_folder = get_asset_folder_path(path, POSTS_DIR)

    if not asset_folder.exists():
        return ApiResponse(success=True, data=[])

    try:
        image_exts = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
        images: List[dict] = []

        for f in sorted(asset_folder.iterdir()):
            if f.is_file() and f.suffix.lower() in image_exts:
                relative = f.relative_to(POSTS_DIR).as_posix()
                url = "/" + f.relative_to(BLOG_ROOT).as_posix()
                images.append(ImageInfo(
                    name=f.name,
                    path=relative,
                    url=url,
                ).model_dump())

        return ApiResponse(success=True, data=images)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图片列表失败: {e}")


@router.delete("/image/{path:path}")
async def delete_image(path: str):
    """删除图片"""
    full_path = POSTS_DIR / path
    if not full_path.exists():
        return ApiResponse(success=False, error="图片不存在")

    try:
        full_path.unlink()
        return ApiResponse(success=True, data={"path": path})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除图片失败: {e}")
