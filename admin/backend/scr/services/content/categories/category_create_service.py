"""Category creation workflow service."""

from typing import Any

from scr.core.config import settings
from scr.core.exceptions import BadRequestError, ConflictError, NotFoundError
from scr.models.article import ArticleType
from scr.schemas.category import CategoryCreateDTO, CategoryDTO
from scr.services.content.categories.category_directory_service import CategoryDirectoryService
from scr.services.content.categories.docs_content_sync_service import DocsContentSyncService
from scr.services.content.categories.category_index_service import CategoryIndexService
from scr.services.content.categories.category_path_service import CategoryPathService
from scr.services.content.categories.category_query_service import CategoryQueryService
from scr.services.content.categories.category_registry_entry_service import CategoryRegistryEntryService
from scr.services.content.categories.category_registry_service import CategoryRegistryService
from scr.services.content.blog.blog_content_sync_service import BlogContentSyncService
from scr.services.content.docusaurus.docusaurus_config_service import DocusaurusConfigService
from scr.services.content.sidebars.sidebar_service import SidebarService


class CategoryCreateService:
    """Coordinate creating category directories and related site metadata."""

    def __init__(self) -> None:
        self.sidebar = SidebarService()
        self.docusaurus_config = DocusaurusConfigService()
        self.category_index = CategoryIndexService()
        self.registry = CategoryRegistryService()
        self.registry_entries = CategoryRegistryEntryService()
        self.directories = CategoryDirectoryService()
        self.paths = CategoryPathService()
        self.query = CategoryQueryService()
        self.blog_sync = BlogContentSyncService()
        self.docs_sync = DocsContentSyncService()

    def create_category(self, payload: CategoryCreateDTO) -> CategoryDTO:
        """Create a category and synchronize registry, sidebars, index, and nav metadata."""
        path = self.paths.normalize_path(payload.path)
        if payload.type == ArticleType.blog and len(path) != 1:
            raise BadRequestError("blog 分类只允许一级目录。", code="invalid_blog_category_depth")

        existing_paths = self.query.existing_category_paths(payload.type)
        if tuple(path) in existing_paths:
            raise ConflictError("分类已存在。", code="category_already_exists")
        if len(path) > 1 and tuple(path[:-1]) not in existing_paths:
            raise NotFoundError("父级分类不存在。", code="parent_category_not_found")

        entries = self._load_registry_entries()
        registry_snapshot = self.snapshot_registry()
        config_snapshot = (
            settings.docusaurus_config_path.read_text(encoding="utf-8")
            if settings.docusaurus_config_path.exists()
            else None
        )
        sidebars_snapshot = settings.sidebars_path.read_text(encoding="utf-8") if settings.sidebars_path.exists() else None
        blog_sidebars_snapshot = (
            settings.blog_sidebars_path.read_text(encoding="utf-8")
            if settings.blog_sidebars_path.exists()
            else None
        )
        blog_index_path = settings.blog_dir / "index.md"
        blog_index_snapshot = blog_index_path.read_text(encoding="utf-8") if blog_index_path.exists() else None
        target_dir = self.directories.category_dir(payload.type, path)
        created_dir = False
        top_index_path = settings.docs_dir / path[0] / "index.md" if payload.type == ArticleType.docs else None
        docs_root_index_path = settings.docs_dir / "index.md" if payload.type == ArticleType.docs else None
        docs_root_index_snapshot = (
            docs_root_index_path.read_text(encoding="utf-8")
            if docs_root_index_path and docs_root_index_path.exists()
            else None
        )
        top_index_snapshot = top_index_path.read_text(encoding="utf-8") if top_index_path and top_index_path.exists() else None

        try:
            entry = self.registry_entries.find_or_create_entry(entries, payload.type, path)
            entry["label"] = payload.label or entry.get("label") or CategoryQueryService.default_label(path[-1])
            entry["description"] = payload.description
            entry["cover"] = payload.cover
            if "sort_order" not in entry or entry.get("sort_order") is None:
                entry["sort_order"] = self.registry_entries.next_sort_order(entries, payload.type, len(path))
            if "enabled" not in entry:
                entry["enabled"] = True

            settings.content_schema_dir.mkdir(parents=True, exist_ok=True)
            self._write_registry_entries(entries)

            if target_dir:
                target_dir.mkdir(parents=True, exist_ok=True)
                created_dir = True
            if payload.type == ArticleType.docs and target_dir:
                labels = [
                    str(item.get("label") or CategoryQueryService.default_label(item_path[-1]))
                    for item_path in [path[: index] for index in range(1, len(path) + 1)]
                    for item in [self.registry_entries.find_or_create_entry(entries, payload.type, item_path)]
                ]
                self.sidebar.ensure_category_path(path, labels)
                if len(path) == 1:
                    label = str(entry["label"])
                    self.category_index.ensure_top_category_index(path[0], label, payload.description)
                    self.docusaurus_config.upsert_knowledge_nav_item(path[0], label)
                self.docs_sync.sync_after_category_change([path], sync_type="docs_category_create")
            if payload.type == ArticleType.blog:
                self.blog_sync.sync_after_category_create(path[0], str(entry["label"]))
        except Exception:
            self.restore_registry(registry_snapshot)
            if config_snapshot is None:
                if settings.docusaurus_config_path.exists():
                    settings.docusaurus_config_path.unlink()
            else:
                settings.docusaurus_config_path.write_text(config_snapshot, encoding="utf-8")
            if sidebars_snapshot is None:
                if settings.sidebars_path.exists():
                    settings.sidebars_path.unlink()
            else:
                settings.sidebars_path.write_text(sidebars_snapshot, encoding="utf-8")
            if blog_sidebars_snapshot is None:
                if settings.blog_sidebars_path.exists():
                    settings.blog_sidebars_path.unlink()
            else:
                settings.blog_sidebars_path.write_text(blog_sidebars_snapshot, encoding="utf-8")
            if blog_index_snapshot is None:
                if blog_index_path.exists():
                    blog_index_path.unlink()
            else:
                blog_index_path.write_text(blog_index_snapshot, encoding="utf-8")
            if top_index_path is not None:
                if top_index_snapshot is None:
                    if top_index_path.exists():
                        top_index_path.unlink()
                else:
                    top_index_path.write_text(top_index_snapshot, encoding="utf-8")
            if docs_root_index_path is not None:
                if docs_root_index_snapshot is None:
                    if docs_root_index_path.exists():
                        docs_root_index_path.unlink()
                else:
                    docs_root_index_path.write_text(docs_root_index_snapshot, encoding="utf-8")
            if created_dir and target_dir and target_dir.exists() and not any(target_dir.iterdir()):
                target_dir.rmdir()
            raise

        updated = self.query.list_categories(article_type=payload.type, include_empty=True, include_counts=True)
        found = CategoryQueryService.find_category_in_tree(updated, path)
        if not found:
            raise NotFoundError("分类不存在。", code="category_not_found")
        return found

    def _load_registry_entries(self) -> list[dict[str, Any]]:
        return self.registry.load_entries()

    def _write_registry_entries(self, entries: list[dict[str, Any]]) -> None:
        self.registry.write_entries(entries)

    def snapshot_registry(self) -> str | None:
        return self.registry.snapshot()

    def restore_registry(self, snapshot: str | None) -> None:
        self.registry.restore(snapshot)
