from __future__ import annotations

import shutil
from pathlib import Path

from blog_admin.core.errors import AppError
from blog_admin.core.path_security import decode_path, resolve_under

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


class AssetRepository:
    def __init__(self, blog_root: Path, posts_dir: Path) -> None:
        self.blog_root = blog_root.resolve()
        self.posts_dir = posts_dir.resolve()

    def resolve_posts_path(self, relative_path: str) -> Path:
        return resolve_under(self.posts_dir, relative_path, label="资源路径")

    def resolve_asset_folder(self, article_path: str) -> Path:
        decoded = decode_path(article_path).replace("\\", "/")
        if decoded.lower().endswith(".md"):
            decoded = decoded[:-3]
        return self.resolve_posts_path(decoded)

    def image_info(self, path: Path) -> dict:
        relative = path.relative_to(self.posts_dir).as_posix()
        return {
            "name": path.name,
            "path": relative,
            "url": "/" + path.relative_to(self.blog_root).as_posix(),
            "size": path.stat().st_size,
        }

    def public_image_info(self, path: Path) -> dict:
        info = self.image_info(path)
        return {"name": info["name"], "path": info["path"], "url": info["url"]}

    def create_folder(self, article_path: str) -> dict:
        asset_folder = self.resolve_asset_folder(article_path)
        if asset_folder.exists():
            raise AppError("ASSET_FOLDER_EXISTS", "资源文件夹已存在", status_code=200)

        asset_folder.mkdir(parents=True, exist_ok=True)
        return {"path": asset_folder.relative_to(self.posts_dir).as_posix()}

    def delete_folder(self, path: str) -> dict:
        full_path = self.resolve_posts_path(path)
        if not full_path.exists():
            raise AppError("ASSET_FOLDER_NOT_FOUND", "资源文件夹不存在", status_code=200)

        shutil.rmtree(full_path, ignore_errors=True)
        return {"path": path}

    def delete_image(self, path: str) -> dict:
        full_path = self.resolve_posts_path(path)
        if not full_path.exists():
            raise AppError("ASSET_IMAGE_NOT_FOUND", "图片不存在", status_code=200)

        full_path.unlink()
        return {"path": path}

    def list_article_images(self, article_path: str) -> list[Path]:
        asset_folder = self.resolve_asset_folder(article_path)
        if not asset_folder.exists():
            return []

        return [
            path
            for path in sorted(asset_folder.iterdir())
            if path.is_file() and path.suffix.lower() in IMAGE_EXTS
        ]

    def list_image_folders(self) -> list[dict]:
        folders: list[dict] = []

        for folder in sorted(path for path in self.posts_dir.rglob("*") if path.is_dir()):
            images = [
                self.image_info(path)
                for path in sorted(folder.iterdir())
                if path.is_file() and path.suffix.lower() in IMAGE_EXTS
            ]
            if not images:
                continue

            folder_path = folder.relative_to(self.posts_dir).as_posix()
            article_path = f"{folder_path}.md"
            if not (self.posts_dir / article_path).exists():
                continue

            folders.append(
                {
                    "folderPath": folder_path,
                    "articlePath": article_path,
                    "articleExists": True,
                    "imageCount": len(images),
                    "images": images,
                }
            )

        return folders

    def get_asset_file(self, path: str) -> Path:
        full_path = self.resolve_posts_path(path)
        if not full_path.exists() or not full_path.is_file():
            raise AppError("ASSET_NOT_FOUND", "资源不存在", status_code=404)
        if full_path.suffix.lower() not in IMAGE_EXTS:
            raise AppError("UNSUPPORTED_ASSET_PREVIEW", "不支持预览该资源类型", status_code=400)
        return full_path
