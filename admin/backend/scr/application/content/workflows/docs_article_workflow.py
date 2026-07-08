"""Docs article workflows."""

from __future__ import annotations

from pathlib import Path

from scr.core.config import settings
from scr.models.article import ArticleType
from scr.schemas.article import ArticleCreateDTO, ArticleDetailDTO
from scr.services.content.articles.article_detail_service import ArticleDetailService
from scr.services.content.articles.article_id_service import ArticleIdService
from scr.services.content.articles.article_summary_service import ArticleSummaryService
from scr.services.content.articles.docs_article_service import DocsArticleService
from scr.services.content.blog.blog_author_service import BlogAuthorService
from scr.services.content.categories.category_index_service import CategoryIndexService
from scr.services.content.categories.docs_content_sync_service import DocsContentSyncService
from scr.services.content.categories.category_service import CategoryService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.filesystem.markdown_service import MarkdownService
from scr.infrastructure.registry.registry_index_service import RegistryIndexService
from scr.services.content.sidebars.sidebar_service import SidebarService
from scr.application.content.workflows.utils import FileSnapshotRollback


class DocsArticleWorkflow:
    """Compose the full create-docs-article business operation."""

    def __init__(self) -> None:
        self.filesystem = FileSystemService()
        self.markdown = MarkdownService()
        self.sidebar = SidebarService()
        self.category = CategoryService()
        self.blog_authors = BlogAuthorService()
        self.article_ids = ArticleIdService()
        self.article_summaries = ArticleSummaryService(
            filesystem=self.filesystem,
            markdown=self.markdown,
            sidebar=self.sidebar,
            category=self.category,
            article_ids=self.article_ids,
        )
        self.article_details = ArticleDetailService(
            filesystem=self.filesystem,
            markdown=self.markdown,
            sidebar=self.sidebar,
            summary=self.article_summaries,
            blog_authors=self.blog_authors,
            article_ids=self.article_ids,
        )
        self.docs_article = DocsArticleService(
            filesystem=self.filesystem,
            markdown=self.markdown,
            category=self.category,
            article_ids=self.article_ids,
            get_article=self.article_details.get_article,
        )
        self.category_index = CategoryIndexService()
        self.registry_index = RegistryIndexService()
        self.docs_sync = DocsContentSyncService(registry_index=self.registry_index)

    def create_article(self, payload: ArticleCreateDTO) -> ArticleDetailDTO:
        """Create a docs article and synchronize docs sidebar/index/admin index."""
        relative_path = "/".join([*payload.category_path, f"{payload.slug}.md"])
        article_path = self.filesystem.resolve_article_path(ArticleType.docs, relative_path)
        rollback = FileSnapshotRollback()
        rollback.snapshot(settings.sidebars_path)
        top_index_path = self._top_index_path(payload.category_path)
        rollback.snapshot(top_index_path)
        rollback.snapshot(settings.docs_dir / "index.md")

        try:
            article = self.docs_article.create_article_file(payload)
            category_labels = self._category_labels_for_path(payload.category_path)
            doc_id = self.sidebar.doc_id_from_relative_path(article.relative_path)
            self.sidebar.ensure_doc_id_in_existing_category(doc_id, category_labels)
            self.docs_sync.sync_after_article_change(
                [article.relative_path],
                sync_type="article_create",
            )
            return article
        except Exception:
            if article_path.exists():
                article_path.unlink()
            rollback.restore_all()
            raise

    @staticmethod
    def _top_index_path(category_path: list[str]) -> Path | None:
        if not category_path:
            return None
        return settings.docs_dir / category_path[0] / "index.md"

    def _category_labels_for_path(self, category_path: list[str]) -> list[str]:
        labels: list[str] = []
        for index in range(1, len(category_path) + 1):
            _path, label = self.category.resolve_article_category(ArticleType.docs, category_path[:index])
            labels.append(label)
        return labels
