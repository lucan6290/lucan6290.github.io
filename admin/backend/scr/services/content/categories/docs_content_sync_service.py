"""Shared docs content synchronization helpers."""

from __future__ import annotations

from scr.core.config import settings


class DocsContentSyncService:
    """Keep derived docs files aligned after content mutations.

    Imports are lazy to avoid CategoryService/CategoryIndexService cycles.
    """

    def __init__(self, *, registry_index: object | None = None) -> None:
        self.registry_index = registry_index

    def sync_after_category_change(
        self,
        affected_category_paths: list[list[str]] | None = None,
        *,
        sync_type: str = "docs_category_change",
    ) -> None:
        """Sync docs indexes and registry after a category mutation."""
        self._sync_indexes(affected_category_paths or [])
        self._rebuild_registry(sync_type)

    def sync_after_article_change(
        self,
        affected_relative_paths: list[str] | None = None,
        *,
        sync_type: str = "docs_article_change",
    ) -> None:
        """Sync docs indexes and registry after an article mutation."""
        category_paths = [
            self._category_path_from_relative_path(relative_path)
            for relative_path in affected_relative_paths or []
        ]
        self._sync_indexes([path for path in category_paths if path])
        self._rebuild_registry(sync_type)

    def _sync_indexes(self, affected_category_paths: list[list[str]]) -> None:
        from scr.services.content.categories.category_index_service import CategoryIndexService

        category_index = CategoryIndexService()
        category_index.sync_root_index(dry_run=False)
        top_slugs = self._top_slugs(affected_category_paths)
        if not top_slugs:
            top_slugs = self._existing_top_slugs()
        for top_slug in top_slugs:
            if not (settings.docs_dir / top_slug).is_dir():
                continue
            category_index.sync_top_category(top_slug, force=True, dry_run=False)

    def _rebuild_registry(self, sync_type: str) -> None:
        if self.registry_index is not None:
            self.registry_index.rebuild(sync_type=sync_type)
            return

        from scr.infrastructure.registry.registry_index_service import RegistryIndexService

        RegistryIndexService().rebuild(sync_type=sync_type)

    @staticmethod
    def _category_path_from_relative_path(relative_path: str) -> list[str]:
        parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
        if not parts:
            return []
        if parts[-1].lower() in {"index.md", "index.mdx"}:
            parts = parts[:-1]
        else:
            parts = parts[:-1]
        return parts

    @staticmethod
    def _top_slugs(category_paths: list[list[str]]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for path in category_paths:
            if not path:
                continue
            top_slug = path[0]
            if top_slug not in seen:
                seen.add(top_slug)
                result.append(top_slug)
        return result

    @staticmethod
    def _existing_top_slugs() -> list[str]:
        if not settings.docs_dir.exists():
            return []
        return sorted(path.name for path in settings.docs_dir.iterdir() if path.is_dir())
