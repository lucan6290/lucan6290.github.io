"""Category deletion workflow service."""

import shutil
from typing import Any

from scr.core.config import settings
from scr.core.exceptions import BadRequestError, NotFoundError
from scr.models.article import ArticleType
from scr.schemas.common import FileChangeDTO, MutationPlanDTO
from scr.services.content.blog.blog_content_sync_service import BlogContentSyncService
from scr.services.content.categories.category_directory_service import CategoryDirectoryService
from scr.services.content.categories.docs_content_sync_service import DocsContentSyncService
from scr.services.content.categories.category_id_service import CategoryIdService
from scr.services.content.categories.category_index_service import CategoryIndexService
from scr.services.content.categories.category_reference_service import CategoryReferenceService
from scr.services.content.categories.category_registry_entry_service import CategoryRegistryEntryService
from scr.services.content.categories.category_registry_service import CategoryRegistryService
from scr.services.content.docusaurus.docusaurus_config_service import DocusaurusConfigService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.services.content.sidebars.sidebar_service import SidebarService


class CategoryDeleteService:
    """Coordinate deleting a category and its related site metadata."""

    def __init__(self) -> None:
        self.filesystem = FileSystemService()
        self.sidebar = SidebarService()
        self.docusaurus_config = DocusaurusConfigService()
        self.category_index = CategoryIndexService()
        self.registry = CategoryRegistryService()
        self.registry_entries = CategoryRegistryEntryService()
        self.directories = CategoryDirectoryService(filesystem=self.filesystem)
        self.references = CategoryReferenceService(filesystem=self.filesystem, sidebar=self.sidebar)
        self.registry_path = settings.content_schema_dir / "categories.yml"
        self.blog_sync = BlogContentSyncService()
        self.docs_sync = DocsContentSyncService()

    def delete_category(
        self,
        category_id: str,
        *,
        dry_run: bool = True,
        confirm: bool = False,
    ) -> MutationPlanDTO:
        """Delete a category directory and sync registry, sidebar, index, and nav metadata."""
        article_type, path = CategoryIdService.decode(category_id)
        if not path:
            raise BadRequestError("分类 ID 无效。", code="category_id_invalid")

        entries = self._load_registry_entries()
        registry_delete_count = self.registry_entries.count_descendants(entries, article_type, path)
        target_dir = self.directories.category_dir(article_type, path)
        has_directory = target_dir.exists() and target_dir.is_dir() if target_dir else False

        if not has_directory and registry_delete_count == 0:
            raise NotFoundError("分类不存在。", code="category_not_found")

        article_files = self.directories.article_files_under_category(article_type, target_dir) if has_directory else []
        doc_ids = [
            self.sidebar.doc_id_from_relative_path(self.filesystem.relative_posix_path(article_type, article_path))
            for article_path in article_files
        ] if article_type == ArticleType.docs else []
        category_labels = self.registry_entries.labels_for_path(entries, article_type, path)
        registered_doc_ids = self.sidebar.list_registered_doc_ids() if doc_ids else set()
        doc_ids_to_remove = [doc_id for doc_id in doc_ids if doc_id in registered_doc_ids]
        external_references = self.references.find_external_article_references(article_type, article_files)
        top_nav_needs_remove = (
            article_type == ArticleType.docs
            and len(path) == 1
            and self.docusaurus_config.knowledge_nav_item_exists(path[0])
        )
        top_index_needs_sync = (
            article_type == ArticleType.docs
            and len(path) > 1
            and (settings.docs_dir / path[0] / "index.md").exists()
        )

        if not dry_run and not confirm:
            raise BadRequestError("删除分类需要显式确认。", code="confirmation_required")

        changes: list[FileChangeDTO] = []
        if has_directory and target_dir:
            changes.append(
                FileChangeDTO(
                    action="delete",
                    target=self.directories.project_relative_posix_path(target_dir),
                    description=(
                        f"删除分类目录及其 {len(article_files)} 篇文章"
                        if dry_run
                        else f"已删除分类目录及其 {len(article_files)} 篇文章"
                    ),
                )
            )

        if doc_ids_to_remove or (article_type == ArticleType.docs and category_labels):
            changes.append(
                FileChangeDTO(
                    action="update",
                    target=self.directories.project_relative_posix_path(settings.sidebars_path),
                    description=(
                        "删除 docs 侧边栏分类结构"
                        if dry_run
                        else "已删除 docs 侧边栏分类结构"
                    ),
                )
            )

        if registry_delete_count:
            changes.append(
                FileChangeDTO(
                    action="update",
                    target=self.directories.project_relative_posix_path(self.registry_path),
                    description=(
                        f"移除 {registry_delete_count} 条分类注册表记录"
                        if dry_run
                        else f"已移除 {registry_delete_count} 条分类注册表记录"
                    ),
                )
            )
        if top_nav_needs_remove:
            changes.append(
                FileChangeDTO(
                    action="delete",
                    target=self.directories.project_relative_posix_path(settings.docusaurus_config_path),
                    description="删除知识库顶部导航一级分类" if dry_run else "已删除知识库顶部导航一级分类",
                )
            )
        if top_index_needs_sync:
            changes.append(
                FileChangeDTO(
                    action="update",
                    target=self.directories.project_relative_posix_path(settings.docs_dir / path[0] / "index.md"),
                    description=(
                        "同步 docs 一级分类目录页"
                        if dry_run
                        else "已同步 docs 一级分类目录页"
                    ),
                )
            )
        if article_type == ArticleType.blog and len(path) == 1:
            changes.extend(
                [
                    FileChangeDTO(
                        action="delete",
                        target=self.directories.project_relative_posix_path(settings.docusaurus_config_path),
                        description="删除博客顶部导航一级分类" if dry_run else "已删除博客顶部导航一级分类",
                    ),
                    FileChangeDTO(
                        action="update",
                        target=self.directories.project_relative_posix_path(settings.blog_sidebars_path),
                        description="同步 blog 侧边栏" if dry_run else "已同步 blog 侧边栏",
                    ),
                    FileChangeDTO(
                        action="update",
                        target=self.directories.project_relative_posix_path(settings.blog_dir / "index.md"),
                        description="同步 blog 总目录页" if dry_run else "已同步 blog 总目录页",
                    ),
                ]
            )

        warnings: list[str] = []
        if external_references:
            warnings.append(
                "其他文章中仍包含被删除分类下文章的旧链接，请删除后手动检查："
                + "、".join(external_references[:10])
                + (" 等" if len(external_references) > 10 else "")
            )
        plan = MutationPlanDTO(
            dry_run=dry_run,
            requires_confirmation=dry_run,
            changes=changes,
            warnings=warnings,
        )

        if dry_run:
            return plan

        if article_type == ArticleType.docs and category_labels:
            removed_category = self.sidebar.remove_category_path(path, category_labels)
            if not removed_category:
                for doc_id in doc_ids_to_remove:
                    self.sidebar.remove_doc_id(doc_id)
        if registry_delete_count:
            settings.content_schema_dir.mkdir(parents=True, exist_ok=True)
            self._write_registry_entries(self.registry_entries.remove_descendants(entries, article_type, path))
        if has_directory and target_dir:
            shutil.rmtree(target_dir)
        if top_index_needs_sync:
            self.category_index.sync_top_category(path[0], force=True, dry_run=False)
        if top_nav_needs_remove:
            self.docusaurus_config.remove_knowledge_nav_item(path[0])
        if article_type == ArticleType.docs:
            self.docs_sync.sync_after_category_change([path], sync_type="docs_category_delete")
        if article_type == ArticleType.blog and len(path) == 1:
            self.blog_sync.sync_after_category_delete(path[0])

        return plan

    def _load_registry_entries(self) -> list[dict[str, Any]]:
        return self.registry.load_entries()

    def _write_registry_entries(self, entries: list[dict[str, Any]]) -> None:
        self.registry.write_entries(entries)
