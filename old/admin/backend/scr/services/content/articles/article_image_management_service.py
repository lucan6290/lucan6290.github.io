"""Article image management use cases."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from scr.core.config import settings
from scr.core.exceptions import BadRequestError, ConflictError, NotFoundError
from scr.core.security import PathSecurityError, ensure_child_path
from scr.schemas.article import ArticleImageCheckDTO, ArticleImageListDTO, ImageDTO
from scr.schemas.common import FileChangeDTO, MutationPlanDTO
from scr.services.content.articles.article_id_service import ArticleIdService
from scr.services.content.articles.article_image_reference_service import ArticleImageReferenceService
from scr.services.content.articles.article_image_service import ArticleImageService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.filesystem.markdown_service import MarkdownService


class ArticleImageManagementService:
    """Manage article-local image files and image reference checks."""

    def __init__(
        self,
        *,
        filesystem: FileSystemService,
        markdown: MarkdownService,
        article_ids: ArticleIdService,
        images: ArticleImageService,
        image_references: ArticleImageReferenceService,
    ) -> None:
        self.filesystem = filesystem
        self.markdown = markdown
        self.article_ids = article_ids
        self.images = images
        self.image_references = image_references

    def list_article_images(self, article_id: str) -> ArticleImageListDTO:
        article_path = self.article_path(article_id)
        parsed = self.markdown.parse(article_path.read_text(encoding="utf-8"))
        image_dir = self.image_dir_for(article_path)
        if not image_dir.exists() or not image_dir.is_dir():
            return ArticleImageListDTO(article_id=article_id, image_dir=None, images=[])

        referenced_sources = self.image_references.referenced_source_set(parsed.body)
        images: list[ImageDTO] = []
        for image_path in self.images.scan_files(image_dir):
            markdown_url = f"./{image_dir.name}/{image_path.name}"
            images.append(
                ImageDTO(
                    name=image_path.name,
                    relative_path=self.project_relative_posix_path(image_path),
                    markdown_url=markdown_url,
                    markdown=f"![{image_path.stem}]({markdown_url})",
                    size=image_path.stat().st_size,
                    referenced=ArticleImageReferenceService.is_referenced(
                        image_dir.name,
                        image_path.name,
                        referenced_sources,
                    ),
                    created_at=self.file_created_at(image_path),
                )
            )

        return ArticleImageListDTO(
            article_id=article_id,
            image_dir=self.project_relative_posix_path(image_dir),
            images=images,
        )

    def upload_article_image(
        self,
        article_id: str,
        *,
        original_filename: str,
        content_type: str | None,
        content: bytes,
        slug: str | None = None,
        alt: str | None = None,
    ) -> ImageDTO:
        article_path = self.article_path(article_id)
        extension = Path(original_filename).suffix.lower()
        if extension not in self.images.allowed_extensions:
            raise BadRequestError("文件类型不允许。", code="unsupported_file_type")
        if len(content) > self.images.max_size_bytes:
            raise BadRequestError(
                "文件超过大小限制。",
                code="file_too_large",
                details={"max_size": self.images.max_size_bytes, "actual_size": len(content)},
            )
        self.images.validate_content(extension, content_type, content)

        safe_stem = self.images.build_safe_stem(slug or Path(original_filename).stem)
        image_dir = self.image_dir_for(article_path)
        image_dir.mkdir(parents=True, exist_ok=True)
        target_path = ArticleImageService.next_available_path(image_dir, safe_stem, extension)
        target_path.write_bytes(content)

        markdown_url = f"./{image_dir.name}/{target_path.name}"
        alt_text = alt.strip() if alt and alt.strip() else target_path.stem
        return ImageDTO(
            name=target_path.name,
            relative_path=self.project_relative_posix_path(target_path),
            markdown_url=markdown_url,
            markdown=f"![{alt_text}]({markdown_url})",
            size=target_path.stat().st_size,
            referenced=False,
            created_at=self.file_created_at(target_path),
        )

    def check_article_images(self, article_id: str) -> ArticleImageCheckDTO:
        article_path = self.article_path(article_id)
        parsed = self.markdown.parse(article_path.read_text(encoding="utf-8"))
        image_dir = self.image_dir_for(article_path)
        image_files = self.images.scan_files(image_dir) if image_dir.exists() and image_dir.is_dir() else []
        referenced_sources = self.image_references.referenced_source_set(parsed.body)
        referenced_images: list[str] = []
        unused_images: list[str] = []

        for image_path in image_files:
            if ArticleImageReferenceService.is_referenced(image_dir.name, image_path.name, referenced_sources):
                referenced_images.append(image_path.name)
            else:
                unused_images.append(image_path.name)

        missing_references, out_of_scope_references = self.image_references.missing_references(article_path, parsed.body)
        return ArticleImageCheckDTO(
            article_id=article_id,
            image_dir=self.project_relative_posix_path(image_dir) if image_dir.exists() and image_dir.is_dir() else None,
            referenced_images=referenced_images,
            unused_images=unused_images,
            missing_references=missing_references,
            out_of_scope_references=out_of_scope_references,
        )

    def get_article_image_path(self, article_id: str, image_name: str) -> Path:
        self.images.validate_name(image_name)
        article_path = self.article_path(article_id)
        return self.safe_existing_image_path(article_path, image_name)

    def delete_article_image(
        self,
        article_id: str,
        image_name: str,
        *,
        dry_run: bool = True,
        confirm: bool = False,
    ) -> MutationPlanDTO:
        self.images.validate_name(image_name)
        article_path = self.article_path(article_id)
        image_dir = self.image_dir_for(article_path)
        image_path = self.safe_existing_image_path(article_path, image_name)

        parsed = self.markdown.parse(article_path.read_text(encoding="utf-8"))
        referenced_sources = self.image_references.referenced_source_set(parsed.body)
        is_referenced = ArticleImageReferenceService.is_referenced(image_dir.name, image_name, referenced_sources)
        warnings = [f"图片 {image_name} 仍被正文引用，删除后文章会出现缺失图片。"] if is_referenced else []

        if not dry_run and is_referenced and not confirm:
            raise ConflictError(
                "图片仍被正文引用，请确认后再删除。",
                code="image_still_referenced",
                details={"image_name": image_name},
            )
        if not dry_run and not confirm:
            raise BadRequestError("删除图片需要显式确认。", code="confirmation_required")

        plan = MutationPlanDTO(
            dry_run=dry_run,
            requires_confirmation=dry_run,
            changes=[
                FileChangeDTO(
                    action="delete",
                    target=self.project_relative_posix_path(image_path),
                    description=(
                        f"删除文章图片 {image_name}"
                        if dry_run
                        else f"已删除文章图片 {image_name}"
                    ),
                )
            ],
            warnings=warnings,
        )

        if dry_run:
            return plan

        image_path.unlink()
        return plan

    def article_path(self, article_id: str) -> Path:
        article_type, relative_path = self.article_ids.decode(article_id)
        path = self.filesystem.resolve_article_path(article_type, relative_path)
        if not path.exists() or not path.is_file():
            raise NotFoundError("文章不存在。", code="article_not_found")
        return path

    def safe_existing_image_path(self, article_path: Path, image_name: str) -> Path:
        image_dir = self.image_dir_for(article_path)
        try:
            image_path = ensure_child_path(image_dir, image_dir / image_name)
        except PathSecurityError as exc:
            raise BadRequestError("图片路径越界，已拒绝访问。", code="path_out_of_scope") from exc

        if not image_path.exists() or not image_path.is_file():
            raise NotFoundError("图片不存在。", code="image_not_found")
        return image_path

    @staticmethod
    def image_dir_for(path: Path) -> Path:
        return path.with_name(f"{path.stem}-imgs")

    @staticmethod
    def file_created_at(path: Path) -> str:
        return datetime.fromtimestamp(path.stat().st_ctime, tz=ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")

    @staticmethod
    def project_relative_posix_path(path: Path) -> str:
        try:
            return path.resolve().relative_to(settings.project_root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()
