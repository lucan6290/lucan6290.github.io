"""Shared blog content synchronization helpers."""

from __future__ import annotations

from scr.core.config import settings


class BlogContentSyncService:
    """Keep derived blog files aligned after content mutations.

    Imports are intentionally lazy: blog index/sidebar services depend on
    CategoryService, and category services use this helper.
    """

    def sync_sidebar_and_index(self, *, sync_type: str = "blog_content_sync") -> None:
        """Rebuild ``blogSidebars.ts`` and the root ``blog/index.md``."""
        from scr.services.content.blog.blog_index_service import BlogIndexService
        from scr.infrastructure.registry.registry_index_service import RegistryIndexService
        from scr.services.content.sidebars.blog_sidebar_service import BlogSidebarService

        blog_sidebar = BlogSidebarService()
        blog_sidebar.write_categories(blog_sidebar.synced_categories())
        BlogIndexService().sync_all(dry_run=False, confirm=True)
        RegistryIndexService().rebuild(sync_type=sync_type)

    def sync_after_category_create(self, slug: str, label: str) -> None:
        """Sync all derived files after a blog top category is created."""
        self._upsert_nav_item(slug, label)
        self.sync_sidebar_and_index(sync_type="blog_category_create")

    def sync_after_category_update(self, slug: str, label: str) -> None:
        """Sync all derived files after a blog top category label changes."""
        self._upsert_nav_item(slug, label)
        self.sync_sidebar_and_index(sync_type="blog_category_update")

    def sync_after_category_rename(self, old_slug: str, new_slug: str, label: str) -> None:
        """Sync all derived files after a blog top category is renamed."""
        if settings.docusaurus_config_path.exists():
            from scr.services.content.docusaurus.docusaurus_config_service import DocusaurusConfigService

            DocusaurusConfigService().replace_blog_nav_item(old_slug, new_slug, label)
        self.sync_sidebar_and_index(sync_type="blog_category_rename")

    def sync_after_category_delete(self, slug: str) -> None:
        """Sync all derived files after a blog top category is deleted."""
        if settings.docusaurus_config_path.exists():
            from scr.services.content.docusaurus.docusaurus_config_service import DocusaurusConfigService

            DocusaurusConfigService().remove_blog_nav_item(slug)
        self.sync_sidebar_and_index(sync_type="blog_category_delete")

    def sync_after_article_change(self, category_slug: str | None = None, category_label: str | None = None) -> None:
        """Sync derived files after a blog article is deleted, moved, or renamed."""
        if category_slug and category_label:
            self._upsert_nav_item(category_slug, category_label)
        self.sync_sidebar_and_index(sync_type="blog_article_change")

    @staticmethod
    def _upsert_nav_item(slug: str, label: str) -> None:
        if not settings.docusaurus_config_path.exists():
            return
        from scr.services.content.blog.blog_nav_service import BlogNavService

        BlogNavService().upsert_top_category(slug, label)
