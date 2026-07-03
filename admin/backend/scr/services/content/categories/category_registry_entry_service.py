"""Category registry entry helpers."""

from __future__ import annotations

from typing import Any

from scr.models.article import ArticleType
from scr.services.content.categories.category_query_service import CategoryQueryService


class CategoryRegistryEntryService:
    """Operate on in-memory category registry entries."""

    def find_or_create_entry(
        self,
        entries: list[dict[str, Any]],
        article_type: ArticleType,
        path: list[str],
    ) -> dict[str, Any]:
        for entry in entries:
            if self.matches(entry, article_type, path):
                return entry

        entry = {
            "type": article_type.value,
            "path": path,
            "slug": path[-1],
            "label": CategoryQueryService.default_label(path[-1]),
            "enabled": True,
        }
        entries.append(entry)
        return entry

    def find_entry(
        self,
        entries: list[dict[str, Any]],
        article_type: ArticleType,
        path: list[str],
    ) -> dict[str, Any] | None:
        for entry in entries:
            if self.matches(entry, article_type, path):
                return entry
        return None

    def labels_for_path(
        self,
        entries: list[dict[str, Any]],
        article_type: ArticleType,
        path: list[str],
    ) -> list[str]:
        return [self.label_for_path(entries, article_type, path[:index]) for index in range(1, len(path) + 1)]

    def label_for_path(
        self,
        entries: list[dict[str, Any]],
        article_type: ArticleType,
        path: list[str],
    ) -> str:
        entry = self.find_entry(entries, article_type, path)
        return str(entry.get("label")) if entry and entry.get("label") else CategoryQueryService.default_label(path[-1])

    def next_sort_order(self, entries: list[dict[str, Any]], article_type: ArticleType, depth: int) -> int:
        orders: list[int] = []
        for entry in entries:
            if str(entry.get("type", ArticleType.docs.value)) != article_type.value:
                continue
            if len(CategoryQueryService.entry_path(entry)) != depth:
                continue
            sort_order = CategoryQueryService.optional_int(entry.get("sort_order"))
            if sort_order is not None:
                orders.append(sort_order)
        return (max(orders) + 10) if orders else depth * 10

    def count_descendants(
        self,
        entries: list[dict[str, Any]],
        article_type: ArticleType,
        category_path: list[str],
    ) -> int:
        return len(entries) - len(self.remove_descendants(entries, article_type, category_path))

    def remove_descendants(
        self,
        entries: list[dict[str, Any]],
        article_type: ArticleType,
        category_path: list[str],
    ) -> list[dict[str, Any]]:
        prefix = tuple(category_path)
        filtered: list[dict[str, Any]] = []
        for entry in entries:
            entry_type = str(entry.get("type", ArticleType.docs.value))
            entry_path = tuple(CategoryQueryService.entry_path(entry))
            if entry_type == article_type.value and entry_path[: len(prefix)] == prefix:
                continue
            filtered.append(entry)
        return filtered

    def rename_descendants(
        self,
        entries: list[dict[str, Any]],
        article_type: ArticleType,
        old_path: list[str],
        new_path: list[str],
        target_label: str | None,
    ) -> list[dict[str, Any]]:
        prefix = tuple(old_path)
        renamed: list[dict[str, Any]] = []
        for entry in entries:
            if str(entry.get("type", ArticleType.docs.value)) != article_type.value:
                renamed.append(entry)
                continue

            entry_path = CategoryQueryService.entry_path(entry)
            if tuple(entry_path[: len(prefix)]) != prefix:
                renamed.append(entry)
                continue

            updated = dict(entry)
            updated_path = [*new_path, *entry_path[len(prefix) :]]
            updated["path"] = updated_path
            updated["slug"] = updated_path[-1]
            if target_label is not None and entry_path == old_path:
                updated["label"] = target_label
            renamed.append(updated)
        return renamed

    @staticmethod
    def matches(entry: dict[str, Any], article_type: ArticleType, path: list[str]) -> bool:
        return str(entry.get("type", ArticleType.docs.value)) == article_type.value and CategoryQueryService.entry_path(entry) == path
