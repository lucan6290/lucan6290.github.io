"""Category update workflow service."""

from __future__ import annotations

from scr.core.config import settings
from scr.core.exceptions import BadRequestError, NotFoundError
from scr.models.article import ArticleType
from scr.schemas.category import CategoryDTO, CategoryUpdateDTO
from scr.services.content.blog.blog_content_sync_service import BlogContentSyncService
from scr.services.content.categories.docs_content_sync_service import DocsContentSyncService
from scr.services.content.categories.category_id_service import CategoryIdService
from scr.services.content.categories.category_query_service import CategoryQueryService
from scr.services.content.categories.category_registry_entry_service import CategoryRegistryEntryService
from scr.services.content.categories.category_registry_service import CategoryRegistryService
from scr.services.content.docusaurus.docusaurus_config_service import DocusaurusConfigService
from scr.services.content.sidebars.sidebar_service import SidebarService


class CategoryUpdateService:
    """Update category display metadata without moving the real directory."""

    def __init__(self) -> None:
        self.docusaurus_config = DocusaurusConfigService()
        self.query = CategoryQueryService()
        self.registry = CategoryRegistryService()
        self.registry_entries = CategoryRegistryEntryService()
        self.blog_sync = BlogContentSyncService()
        self.docs_sync = DocsContentSyncService()
        self.sidebar = SidebarService()

    def update_category(self, category_id: str, payload: CategoryUpdateDTO) -> CategoryDTO:
        article_type, path = CategoryIdService.decode(category_id)
        if not path:
            raise BadRequestError("分类 ID 无效。", code="category_id_invalid")

        existing_paths = self.query.existing_category_paths(article_type)
        if tuple(path) not in existing_paths:
            raise NotFoundError("分类不存在。", code="category_not_found")

        entries = self.registry.load_entries()
        old_labels = self.registry_entries.labels_for_path(entries, article_type, path)
        entry = self.registry_entries.find_or_create_entry(entries, article_type, path)
        if payload.label is not None:
            entry["label"] = payload.label
        if payload.description is not None:
            entry["description"] = payload.description
        if payload.cover is not None:
            entry["cover"] = payload.cover

        settings.content_schema_dir.mkdir(parents=True, exist_ok=True)
        self.registry.write_entries(entries)
        if article_type == ArticleType.docs and len(path) == 1 and payload.label is not None:
            self.docusaurus_config.update_knowledge_nav_item_label(path[0], payload.label)
        if article_type == ArticleType.docs:
            if payload.label is not None:
                new_labels = self.registry_entries.labels_for_path(entries, article_type, path)
                self.sidebar.rename_category_path(path, path, old_labels, new_labels)
            self.docs_sync.sync_after_category_change([path], sync_type="docs_category_update")
        if (
            article_type == ArticleType.blog
            and len(path) == 1
            and (payload.label is not None or payload.description is not None)
        ):
            self.blog_sync.sync_after_category_update(path[0], str(entry["label"]))

        updated = self.query.list_categories(article_type=article_type, include_empty=True, include_counts=True)
        found = CategoryQueryService.find_category_in_tree(updated, path)
        if not found:
            raise NotFoundError("分类不存在。", code="category_not_found")
        return found
