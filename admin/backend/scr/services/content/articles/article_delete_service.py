"""Article delete use cases."""

from __future__ import annotations

from pathlib import Path
import shutil

from scr.core.config import settings
from scr.core.exceptions import BadRequestError, ConflictError, NotFoundError
from scr.core.security import ensure_child_path
from scr.models.article import ArticleType
from scr.schemas.common import FileChangeDTO, MutationPlanDTO
from scr.services.content.articles.article_category_index_sync_service import ArticleCategoryIndexSyncService
from scr.services.content.articles.article_id_service import ArticleIdService
from scr.services.content.articles.article_reference_service import ArticleReferenceService
from scr.services.content.blog.blog_content_sync_service import BlogContentSyncService
from scr.services.content.categories.category_index_service import CategoryIndexService
from scr.services.content.categories.docs_content_sync_service import DocsContentSyncService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.filesystem.markdown_service import MarkdownService
from scr.services.content.sidebars.sidebar_service import SidebarService


class ArticleDeleteService:
    """Delete article files while keeping related metadata in sync."""

    def __init__(
        self,
        *,
        filesystem: FileSystemService,
        markdown: MarkdownService,
        sidebar: SidebarService,
        category_index: CategoryIndexService,
        article_ids: ArticleIdService,
        article_references: ArticleReferenceService,
        category_index_sync: ArticleCategoryIndexSyncService,
    ) -> None:
        self.filesystem = filesystem
        self.markdown = markdown
        self.sidebar = sidebar
        self.category_index = category_index
        self.article_ids = article_ids
        self.article_references = article_references
        self.category_index_sync = category_index_sync
        self.blog_sync = BlogContentSyncService()
        self.docs_sync = DocsContentSyncService()

    def delete_article(
        self,
        article_id: str,
        *,
        with_images: bool = False,
        dry_run: bool = True,
        confirm: bool = False,
    ) -> MutationPlanDTO:
        article_type, relative_path = self.article_ids.decode(article_id)
        article_path = self.filesystem.resolve_article_path(article_type, relative_path)
        if not article_path.exists() or not article_path.is_file():
            raise NotFoundError("文章不存在。", code="article_not_found")

        parsed = self.markdown.parse(article_path.read_text(encoding="utf-8"))
        image_dir = self.image_dir_for(article_path)
        has_image_dir = image_dir.exists() and image_dir.is_dir()
        doc_id = self.sidebar.doc_id_from_relative_path(relative_path) if article_type == ArticleType.docs else None
        sidebar_registered = doc_id in self.sidebar.list_registered_doc_ids() if doc_id else False
        reference_candidates = self.article_references.article_reference_candidates(
            article_type,
            relative_path,
            parsed.frontmatter,
        )
        references = self.article_references.find_article_references(article_type, relative_path, reference_candidates)

        if not dry_run and references and not confirm:
            raise ConflictError(
                "文章仍被站内内容引用，请确认后再删除。",
                code="article_has_references",
                details={"references": references},
            )
        if not dry_run and not confirm:
            raise BadRequestError("删除文章需要显式确认。", code="confirmation_required")

        changes = [
            FileChangeDTO(
                action="delete",
                target=self.filesystem.project_relative_posix_path(article_path),
                description="删除文章文件" if dry_run else "已删除文章文件",
            )
        ]

        if doc_id and sidebar_registered:
            changes.append(
                FileChangeDTO(
                    action="update",
                    target=self.filesystem.project_relative_posix_path(settings.sidebars_path),
                    description=(
                        f"移除 docs 文章 ID {doc_id}"
                        if dry_run
                        else f"已移除 docs 文章 ID {doc_id}"
                    ),
                )
            )

        warnings: list[str] = []
        if has_image_dir and with_images:
            changes.append(
                FileChangeDTO(
                    action="delete",
                    target=self.filesystem.project_relative_posix_path(image_dir),
                    description="删除文章图片目录" if dry_run else "已删除文章图片目录",
                )
            )
        elif has_image_dir:
            warnings.append("文章图片目录存在，默认不会删除，除非 with_images=true。")

        if references:
            warnings.append("文章仍被站内内容引用，删除前请确认引用影响。")
        if article_type == ArticleType.docs:
            changes.extend(self.category_index_sync.preview_changes([relative_path]))
        if article_type == ArticleType.blog:
            changes.extend(
                [
                    FileChangeDTO(
                        action="update",
                        target=self.filesystem.project_relative_posix_path(settings.blog_sidebars_path),
                        description="同步 blog 侧边栏" if dry_run else "已同步 blog 侧边栏",
                    ),
                    FileChangeDTO(
                        action="update",
                        target=self.filesystem.project_relative_posix_path(settings.blog_dir / "index.md"),
                        description="同步 blog 总目录页" if dry_run else "已同步 blog 总目录页",
                    ),
                ]
            )

        plan = MutationPlanDTO(
            dry_run=dry_run,
            requires_confirmation=dry_run,
            changes=changes,
            warnings=warnings,
        )

        if dry_run:
            return plan

        if doc_id and sidebar_registered:
            self.sidebar.remove_doc_id(doc_id)
        if has_image_dir and with_images:
            safe_image_dir = ensure_child_path(article_path.parent, image_dir)
            shutil.rmtree(safe_image_dir)
        article_path.unlink()
        if article_type == ArticleType.docs:
            self.category_index.remove_doc_link(relative_path)
            self.docs_sync.sync_after_article_change(
                [relative_path],
                sync_type="docs_article_delete",
            )
        if article_type == ArticleType.blog:
            self.blog_sync.sync_after_article_change()
        return plan

    @staticmethod
    def image_dir_for(path: Path) -> Path:
        return path.with_name(f"{path.stem}-imgs")
