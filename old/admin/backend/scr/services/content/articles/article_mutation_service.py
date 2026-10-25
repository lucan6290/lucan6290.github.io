"""Article save and delete operations."""

from __future__ import annotations

from collections.abc import Callable

from scr.schemas.article import ArticleDetailDTO, ArticleUpdateDTO
from scr.schemas.common import MutationPlanDTO
from scr.services.content.articles.article_category_index_sync_service import ArticleCategoryIndexSyncService
from scr.services.content.articles.article_delete_service import ArticleDeleteService
from scr.services.content.articles.article_id_service import ArticleIdService
from scr.services.content.articles.article_path_service import ArticlePathService
from scr.services.content.articles.article_reference_service import ArticleReferenceService
from scr.services.content.articles.article_save_service import ArticleSaveService
from scr.services.content.articles.article_summary_service import ArticleSummaryService
from scr.services.content.blog.blog_author_service import BlogAuthorService
from scr.services.content.categories.category_index_service import CategoryIndexService
from scr.services.content.categories.category_service import CategoryService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.filesystem.markdown_service import MarkdownService
from scr.services.content.sidebars.sidebar_service import SidebarService


class ArticleMutationService:
    """Save and delete articles while keeping surrounding metadata in sync."""

    def __init__(
        self,
        *,
        filesystem: FileSystemService | None = None,
        markdown: MarkdownService | None = None,
        sidebar: SidebarService | None = None,
        category: CategoryService | None = None,
        category_index: CategoryIndexService | None = None,
        article_ids: ArticleIdService | None = None,
        article_paths: ArticlePathService | None = None,
        article_summaries: ArticleSummaryService | None = None,
        article_references: ArticleReferenceService | None = None,
        category_index_sync: ArticleCategoryIndexSyncService | None = None,
        article_delete: ArticleDeleteService | None = None,
        article_save: ArticleSaveService | None = None,
        blog_authors: BlogAuthorService | None = None,
        get_article: Callable[[str], ArticleDetailDTO] | None = None,
    ) -> None:
        self.filesystem = filesystem or FileSystemService()
        self.markdown = markdown or MarkdownService()
        self.sidebar = sidebar or SidebarService()
        self.category = category or CategoryService()
        self.category_index = category_index or CategoryIndexService()
        self.article_ids = article_ids or ArticleIdService()
        self.article_paths = article_paths or ArticlePathService()
        self.article_summaries = article_summaries or ArticleSummaryService(
            filesystem=self.filesystem,
            markdown=self.markdown,
            sidebar=self.sidebar,
            category=self.category,
            article_ids=self.article_ids,
        )
        self.article_references = article_references or ArticleReferenceService(
            filesystem=self.filesystem,
            sidebar=self.sidebar,
            summary=self.article_summaries,
        )
        self.category_index_sync = category_index_sync or ArticleCategoryIndexSyncService(
            category=self.category,
            category_index=self.category_index,
        )
        self.article_delete = article_delete or ArticleDeleteService(
            filesystem=self.filesystem,
            markdown=self.markdown,
            sidebar=self.sidebar,
            category_index=self.category_index,
            article_ids=self.article_ids,
            article_references=self.article_references,
            category_index_sync=self.category_index_sync,
        )
        self.blog_authors = blog_authors or BlogAuthorService()
        self._get_article = get_article
        self.article_save = article_save or ArticleSaveService(
            filesystem=self.filesystem,
            markdown=self.markdown,
            article_ids=self.article_ids,
            article_paths=self.article_paths,
            article_summaries=self.article_summaries,
            category_index_sync=self.category_index_sync,
            blog_authors=self.blog_authors,
            get_article=self._get_article,
        )

    def save_article(self, article_id: str, payload: ArticleUpdateDTO) -> ArticleDetailDTO:
        """保存文章内容，不改变文章路径，并使用 expected_version 做乐观锁校验。"""
        return self.article_save.save_article(article_id, payload)

    def delete_article(
        self,
        article_id: str,
        *,
        with_images: bool = False,
        dry_run: bool = True,
        confirm: bool = False,
    ) -> MutationPlanDTO:
        """删除文章文件；docs 文章会同步移除 sidebars.ts 中的 doc_id。"""
        return self.article_delete.delete_article(
            article_id,
            with_images=with_images,
            dry_run=dry_run,
            confirm=confirm,
        )
