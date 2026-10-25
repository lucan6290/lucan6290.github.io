"""Blog article workflows."""

from __future__ import annotations

from scr.core.config import settings
from scr.models.article import ArticleType
from scr.schemas.article import ArticleCreateDTO, ArticleDetailDTO
from scr.services.content.articles.article_detail_service import ArticleDetailService
from scr.services.content.articles.article_id_service import ArticleIdService
from scr.services.content.articles.article_path_service import ArticlePathService
from scr.services.content.articles.article_summary_service import ArticleSummaryService
from scr.services.content.articles.blog_article_service import BlogArticleService
from scr.services.content.blog.blog_author_service import BlogAuthorService
from scr.services.content.blog.blog_index_service import BlogIndexService
from scr.services.content.blog.blog_nav_service import BlogNavService
from scr.services.content.sidebars.blog_sidebar_service import BlogSidebarService
from scr.services.content.categories.category_service import CategoryService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.filesystem.markdown_service import MarkdownService
from scr.infrastructure.registry.registry_index_service import RegistryIndexService
from scr.infrastructure.registry.tag_service import TagService
from scr.services.content.sidebars.sidebar_service import SidebarService
from scr.application.content.workflows.utils import FileSnapshotRollback


class BlogArticleWorkflow:
    """Compose the full create-blog-article business operation."""

    def __init__(self) -> None:
        self.filesystem = FileSystemService()
        self.markdown = MarkdownService()
        self.sidebar = SidebarService()
        self.category = CategoryService()
        self.blog_authors = BlogAuthorService()
        self.article_ids = ArticleIdService()
        self.article_paths = ArticlePathService()
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
        self.blog_article = BlogArticleService(
            filesystem=self.filesystem,
            markdown=self.markdown,
            blog_authors=self.blog_authors,
            article_ids=self.article_ids,
            article_paths=self.article_paths,
            get_article=self.article_details.get_article,
        )
        self.tags = TagService()
        self.blog_index = BlogIndexService()
        self.blog_sidebar = BlogSidebarService()
        self.blog_nav = BlogNavService()
        self.registry_index = RegistryIndexService()

    def create_article(self, payload: ArticleCreateDTO) -> ArticleDetailDTO:
        """Create a blog article and synchronize all derived blog/admin indexes."""
        self.article_paths.validate_path_segment(payload.slug, field_name="slug")
        self.article_paths.validate_blog_category_path(payload.category_path)
        self.blog_authors.validate_authors(payload.authors)

        category_slug = payload.category_path[0]
        relative_path = f"{category_slug}/{payload.slug}.md"
        article_path = self.filesystem.resolve_article_path(ArticleType.blog, relative_path)
        category_dir = settings.blog_dir / category_slug
        category_existed_before = category_dir.exists()

        category_registry_snapshot = self.category.snapshot_registry()
        rollback = FileSnapshotRollback()
        tag_registry_path = settings.content_schema_dir / "tags.yml"
        rollback.snapshot(tag_registry_path)
        blog_index_path = settings.blog_dir / "index.md"
        rollback.snapshot(blog_index_path)
        rollback.snapshot(settings.blog_sidebars_path)
        rollback.snapshot(settings.docusaurus_config_path)

        try:
            self.tags.ensure_tags(payload.tags)
            category_labels = self.category.ensure_category_path(ArticleType.blog, payload.category_path)
            article = self.blog_article.create_article_file(payload)
            category_label = category_labels[0] if category_labels else category_slug
            self._sync_blog_indexes(category_slug, category_label)
            return article
        except Exception:
            if article_path.exists():
                article_path.unlink()
            if not category_existed_before and category_dir.exists() and not any(category_dir.iterdir()):
                category_dir.rmdir()
            self.category.restore_registry(category_registry_snapshot)
            rollback.restore_all()
            raise

    def _sync_blog_indexes(self, category_slug: str, category_label: str) -> None:
        if settings.docusaurus_config_path.exists():
            self.blog_nav.upsert_top_category(category_slug, category_label)
        self.blog_sidebar.write_categories(self.blog_sidebar.synced_categories())
        self.blog_index.sync_all(dry_run=False, confirm=True)
        self.registry_index.rebuild(sync_type="article_create")
