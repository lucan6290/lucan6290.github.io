"""Category rename workflow service."""

import shutil
from typing import Any

from scr.core.config import settings
from scr.core.exceptions import BadRequestError, ConflictError, NotFoundError
from scr.models.article import ArticleType
from scr.schemas.category import CategoryRenameDTO
from scr.schemas.common import FileChangeDTO, MutationPlanDTO
from scr.services.content.blog.blog_content_sync_service import BlogContentSyncService
from scr.services.content.categories.category_directory_service import CategoryDirectoryService
from scr.services.content.categories.docs_content_sync_service import DocsContentSyncService
from scr.services.content.categories.category_id_service import CategoryIdService
from scr.services.content.categories.category_path_service import CategoryPathService
from scr.services.content.categories.category_query_service import CategoryQueryService
from scr.services.content.categories.category_reference_service import CategoryReferenceService
from scr.services.content.categories.category_registry_entry_service import CategoryRegistryEntryService
from scr.services.content.categories.category_registry_service import CategoryRegistryService
from scr.services.content.docusaurus.docusaurus_config_service import DocusaurusConfigService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.services.content.sidebars.sidebar_service import SidebarService


class CategoryRenameService:
    """Coordinate renaming category paths and related metadata."""

    def __init__(self) -> None:
        self.filesystem = FileSystemService()
        self.sidebar = SidebarService()
        self.docusaurus_config = DocusaurusConfigService()
        self.registry = CategoryRegistryService()
        self.registry_entries = CategoryRegistryEntryService()
        self.directories = CategoryDirectoryService(filesystem=self.filesystem)
        self.references = CategoryReferenceService(filesystem=self.filesystem, sidebar=self.sidebar)
        self.query = CategoryQueryService()
        self.registry_path = settings.content_schema_dir / "categories.yml"
        self.blog_sync = BlogContentSyncService()
        self.docs_sync = DocsContentSyncService()

    def rename_category(self, category_id: str, payload: CategoryRenameDTO) -> MutationPlanDTO:
        """Rename a category path and synchronize docs directory, sidebar, registry, and links."""
        article_type, path = CategoryIdService.decode(category_id)
        if not path:
            raise BadRequestError("分类 ID 无效。", code="category_id_invalid")

        CategoryPathService.validate_slug(payload.target_slug)
        target_path = [*path[:-1], payload.target_slug]
        if target_path == path and payload.target_label is None:
            raise BadRequestError("目标分类路径与当前路径一致。", code="category_target_unchanged")

        existing_paths = self.query.existing_category_paths(article_type)
        if tuple(path) not in existing_paths:
            raise NotFoundError("分类不存在。", code="category_not_found")
        if tuple(target_path) != tuple(path) and tuple(target_path) in existing_paths:
            raise ConflictError("目标分类已存在。", code="category_target_exists")

        entries = self._load_registry_entries()
        registry_rename_count = self.registry_entries.count_descendants(entries, article_type, path)
        registry_will_write = registry_rename_count > 0 or payload.target_label is not None
        source_dir = self.directories.category_dir(article_type, path)
        target_dir = self.directories.category_dir(article_type, target_path)
        has_directory = source_dir.exists() and source_dir.is_dir() if source_dir else False
        if has_directory and target_dir and target_dir.exists():
            raise ConflictError("目标分类目录已存在。", code="category_target_dir_exists")

        article_files = self.directories.article_files_under_category(article_type, source_dir) if has_directory else []
        old_category_labels = self.registry_entries.labels_for_path(entries, article_type, path)
        target_label = payload.target_label or self.registry_entries.label_for_path(entries, article_type, target_path)
        new_category_labels = [*self.registry_entries.labels_for_path(entries, article_type, path[:-1]), target_label]
        sidebar_replacements: list[tuple[str, str]] = []
        if article_type == ArticleType.docs and article_files:
            registered_doc_ids = self.sidebar.list_registered_doc_ids()
            for article_path in article_files:
                old_relative_path = self.filesystem.relative_posix_path(article_type, article_path)
                new_relative_path = self.references.renamed_relative_path(old_relative_path, path, target_path)
                old_doc_id = self.sidebar.doc_id_from_relative_path(old_relative_path)
                new_doc_id = self.sidebar.doc_id_from_relative_path(new_relative_path)
                if old_doc_id in registered_doc_ids and old_doc_id != new_doc_id:
                    sidebar_replacements.append((old_doc_id, new_doc_id))

        link_replacements = self.references.category_link_replacements(article_type, path, target_path, article_files)
        link_targets = self.references.find_link_replacement_targets(link_replacements) if payload.replace_links else []
        top_nav_needs_update = (
            article_type == ArticleType.docs
            and len(path) == 1
            and self.docusaurus_config.knowledge_nav_item_exists(path[0])
        )

        if not payload.dry_run and not payload.confirm:
            raise BadRequestError("重命名分类需要显式确认。", code="confirmation_required")

        changes: list[FileChangeDTO] = []
        if has_directory and source_dir and target_dir and source_dir != target_dir:
            changes.append(
                FileChangeDTO(
                    action="move",
                    target=self.directories.project_relative_posix_path(target_dir),
                    from_=self.directories.project_relative_posix_path(source_dir),
                    to=self.directories.project_relative_posix_path(target_dir),
                    description="移动分类目录" if payload.dry_run else "已移动分类目录",
                )
            )
        if sidebar_replacements:
            changes.append(
                FileChangeDTO(
                    action="replace",
                    target=self.directories.project_relative_posix_path(settings.sidebars_path),
                    description=(
                        f"替换 {len(sidebar_replacements)} 个 docs 侧边栏文章 ID"
                        if payload.dry_run
                        else f"已替换 {len(sidebar_replacements)} 个 docs 侧边栏文章 ID"
                    ),
                )
            )
        if article_type == ArticleType.docs:
            changes.append(
                FileChangeDTO(
                    action="update",
                    target=self.directories.project_relative_posix_path(settings.sidebars_path),
                    description="同步 docs 侧边栏分类结构" if payload.dry_run else "已同步 docs 侧边栏分类结构",
                )
            )
        if registry_will_write:
            changes.append(
                FileChangeDTO(
                    action="update",
                    target=self.directories.project_relative_posix_path(self.registry_path),
                    description=(
                        f"更新 {registry_rename_count or 1} 条分类注册表记录"
                        if payload.dry_run
                        else f"已更新 {registry_rename_count or 1} 条分类注册表记录"
                    ),
                )
            )
        if payload.replace_links and link_targets:
            changes.append(
                FileChangeDTO(
                    action="replace",
                    target="site/docs, site/blog",
                    description=(
                        f"替换 {len(link_targets)} 篇文章中的旧分类链接"
                        if payload.dry_run
                        else f"已替换 {len(link_targets)} 篇文章中的旧分类链接"
                    ),
                )
            )
        if top_nav_needs_update:
            changes.append(
                FileChangeDTO(
                    action="update",
                    target=self.directories.project_relative_posix_path(settings.docusaurus_config_path),
                    description="更新知识库顶部导航一级分类" if payload.dry_run else "已更新知识库顶部导航一级分类",
                )
            )
        if article_type == ArticleType.blog and len(path) == 1:
            changes.extend(
                [
                    FileChangeDTO(
                        action="update",
                        target=self.directories.project_relative_posix_path(settings.docusaurus_config_path),
                        description="更新博客顶部导航一级分类" if payload.dry_run else "已更新博客顶部导航一级分类",
                    ),
                    FileChangeDTO(
                        action="update",
                        target=self.directories.project_relative_posix_path(settings.blog_sidebars_path),
                        description="同步 blog 侧边栏" if payload.dry_run else "已同步 blog 侧边栏",
                    ),
                    FileChangeDTO(
                        action="update",
                        target=self.directories.project_relative_posix_path(settings.blog_dir / "index.md"),
                        description="同步 blog 总目录页" if payload.dry_run else "已同步 blog 总目录页",
                    ),
                ]
            )

        warnings: list[str] = []
        if not payload.replace_links and self.references.find_link_replacement_targets(link_replacements):
            warnings.append("站内旧分类链接不会自动替换，除非 replace_links=true。")
        plan = MutationPlanDTO(
            dry_run=payload.dry_run,
            requires_confirmation=payload.dry_run,
            changes=changes,
            warnings=warnings,
        )
        if payload.dry_run:
            return plan

        if article_type == ArticleType.docs:
            sidebar_changed = self.sidebar.rename_category_path(path, target_path, old_category_labels, new_category_labels)
            if not sidebar_changed:
                for old_doc_id, new_doc_id in sidebar_replacements:
                    self.sidebar.replace_doc_id(old_doc_id, new_doc_id)

        updated_entries = entries
        if registry_will_write:
            updated_entries = self.registry_entries.rename_descendants(
                entries,
                article_type,
                path,
                target_path,
                payload.target_label,
            )
            if payload.target_label is not None:
                entry = self.registry_entries.find_or_create_entry(updated_entries, article_type, target_path)
                entry["label"] = payload.target_label
            settings.content_schema_dir.mkdir(parents=True, exist_ok=True)
            self._write_registry_entries(updated_entries)

        if payload.replace_links:
            self.references.replace_article_links(link_replacements)

        if has_directory and source_dir and target_dir and source_dir != target_dir:
            target_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_dir), str(target_dir))

        if top_nav_needs_update:
            label = payload.target_label
            if label is None:
                entry = self.registry_entries.find_entry(updated_entries, article_type, target_path)
                label = str(entry.get("label")) if entry and entry.get("label") else CategoryQueryService.default_label(target_path[-1])
            self.docusaurus_config.replace_knowledge_nav_item(path[0], target_path[0], label)
        if article_type == ArticleType.docs:
            self.docs_sync.sync_after_category_change(
                [path, target_path],
                sync_type="docs_category_rename",
            )
        if article_type == ArticleType.blog and len(path) == 1:
            label = payload.target_label
            if label is None:
                entry = self.registry_entries.find_entry(updated_entries, article_type, target_path)
                label = str(entry.get("label")) if entry and entry.get("label") else CategoryQueryService.default_label(target_path[-1])
            self.blog_sync.sync_after_category_rename(path[0], target_path[0], label)

        return plan

    def _load_registry_entries(self) -> list[dict[str, Any]]:
        return self.registry.load_entries()

    def _write_registry_entries(self, entries: list[dict[str, Any]]) -> None:
        self.registry.write_entries(entries)
