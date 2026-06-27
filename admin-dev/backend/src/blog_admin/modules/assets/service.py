from __future__ import annotations

from pathlib import Path

from blog_admin.core.errors import AppError

from .image_naming import ImageNamingService
from .repository import IMAGE_EXTS, AssetRepository
from .scanner import AssetReferenceScanner


class AssetService:
    def __init__(self, blog_root: Path, posts_dir: Path) -> None:
        self.repository = AssetRepository(blog_root, posts_dir)
        self.scanner = AssetReferenceScanner(self.repository)
        self.image_naming = ImageNamingService(self.repository)

    def resolve_posts_path(self, relative_path: str) -> Path:
        return self.repository.resolve_posts_path(relative_path)

    def resolve_asset_folder(self, article_path: str) -> Path:
        return self.repository.resolve_asset_folder(article_path)

    def image_info(self, path: Path) -> dict:
        return self.repository.image_info(path)

    def create_folder(self, article_path: str) -> dict:
        return self.repository.create_folder(article_path)

    def delete_folder(self, path: str) -> dict:
        return self.repository.delete_folder(path)

    def upload_image(self, article_path: str, image_data: str, extension: str) -> dict:
        image_ext = "." + extension.lower().lstrip(".")
        if image_ext not in IMAGE_EXTS:
            raise AppError("UNSUPPORTED_IMAGE_TYPE", f"不支持的图片格式: {extension}", status_code=200)

        asset_folder = self.resolve_asset_folder(article_path)
        asset_folder.mkdir(parents=True, exist_ok=True)

        image_name = self.image_naming.build_image_name(article_path, image_ext)
        image_path = asset_folder / image_name

        try:
            image_bytes = self.decode_image_data(image_data)
        except Exception as exc:
            raise AppError("INVALID_IMAGE_DATA", "图片 Base64 数据无效", status_code=200) from exc
        image_path.write_bytes(image_bytes)

        info = self.image_info(image_path)
        return {"name": info["name"], "path": info["path"], "url": info["url"]}

    def list_images(self, article_path: str) -> list[dict]:
        return [self.repository.public_image_info(path) for path in self.list_article_images(article_path)]

    def delete_image(self, path: str) -> dict:
        return self.repository.delete_image(path)

    def list_image_folders(self) -> list[dict]:
        return self.repository.list_image_folders()

    def list_unused_images(self, article_path: str, markdown: str) -> list[dict]:
        return self.scanner.list_unused_images(article_path, markdown)

    def delete_unused_images(self, article_path: str, markdown: str) -> list[dict]:
        return self.scanner.delete_unused_images(article_path, markdown)

    def list_article_images(self, article_path: str) -> list[Path]:
        return self.repository.list_article_images(article_path)

    def get_next_image_number(self, article_path: str) -> int:
        return self.image_naming.get_next_image_number(article_path)

    def get_asset_file(self, path: str) -> Path:
        return self.repository.get_asset_file(path)

    @staticmethod
    def decode_image_data(image_data: str) -> bytes:
        return ImageNamingService.decode_image_data(image_data)
