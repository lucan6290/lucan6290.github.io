"""Synchronize admin backend index files from actual site content."""

from __future__ import annotations

import difflib
from typing import Any

import yaml

from scr.core.config import settings
from scr.core.exceptions import BadRequestError
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.registry.registry_index_service import RegistryIndexService
from scr.models.article import ArticleType
from scr.schemas.common import FileChangeDTO, MutationPlanDTO
from scr.services.content.categories.category_registry_entry_service import CategoryRegistryEntryService
from scr.services.content.categories.category_registry_service import CategoryRegistryService
from scr.services.content.sync.site_content_scanner import SiteCategorySnapshot, SiteContentScanner


class BackendIndexSyncService:
    """Update ``categories.yml`` and rebuild ``registry_index.sqlite3``."""

    def __init__(self) -> None:
        self.scanner = SiteContentScanner()
        self.category_registry = CategoryRegistryService()
        self.category_entries = CategoryRegistryEntryService()
        self.registry_index = RegistryIndexService()
        self.filesystem = FileSystemService()

    def sync(self, *, dry_run: bool = True, confirm: bool = False) -> MutationPlanDTO:
        """Synchronize backend registry files from real docs/blog content."""
        if not dry_run and not confirm:
            raise BadRequestError("重建 backend 索引需要显式确认。", code="confirmation_required")

        snapshot = self.scanner.scan()
        existing_entries = self.category_registry.load_entries()
        next_entries, dropped_entries = self._merge_categories(existing_entries, list(snapshot.categories))
        current_content = self._registry_content(existing_entries)
        next_content = self._registry_content(next_entries)

        changes: list[FileChangeDTO] = []
        categories_target = self.filesystem.project_relative_posix_path(self.category_registry.registry_path)
        sqlite_target = self.filesystem.project_relative_posix_path(settings.registry_index_path)
        if current_content != next_content:
            action = "update" if self.category_registry.registry_path.exists() else "create"
            changes.append(
                FileChangeDTO(
                    action=action,
                    target=categories_target,
                    description=(
                        f"根据 site/docs 与 site/blog 重建分类注册表（{len(next_entries)} 个分类）"
                        if dry_run
                        else f"已根据 site/docs 与 site/blog 重建分类注册表（{len(next_entries)} 个分类）"
                    ),
                )
            )
        changes.append(
            FileChangeDTO(
                action="update" if settings.registry_index_path.exists() else "create",
                target=sqlite_target,
                description="重建 registry_index.sqlite3" if dry_run else "已重建 registry_index.sqlite3",
            )
        )

        warnings = [
            f"分类「{self._entry_label(entry)}」在实际内容中不存在，重建时将被移除。"
            for entry in dropped_entries
        ]
        diff = self._unified_diff(current_content, next_content, categories_target) if current_content != next_content else None

        plan = MutationPlanDTO(
            dry_run=dry_run,
            requires_confirmation=dry_run,
            changes=changes,
            warnings=warnings,
            diff=diff,
        )
        if dry_run:
            return plan

        self.category_registry.write_entries(next_entries)
        self.registry_index.rebuild(sync_type="backend_index")
        return plan

    def _merge_categories(
        self,
        existing_entries: list[dict[str, Any]],
        actual_categories: list[SiteCategorySnapshot],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        existing_by_key = {
            self._entry_key(entry): entry
            for entry in existing_entries
            if self._entry_key(entry)
        }
        result: list[dict[str, Any]] = []
        kept_keys: set[str] = set()
        for category in sorted(
            actual_categories,
            key=lambda item: (0 if item.type == ArticleType.docs else 1, len(item.path), "/".join(item.path)),
        ):
            key = self._category_key(category.type, list(category.path))
            existing = dict(existing_by_key.get(key) or {})
            entry = self._normalized_entry(existing, category, existing_entries)
            result.append(entry)
            kept_keys.add(key)

        # 现有注册表里、但实际内容中已不存在的分类，仍按「内容为事实源」原则丢弃，但返回给调用方用于告警。
        dropped = [entry for key, entry in existing_by_key.items() if key not in kept_keys]
        return result, dropped

    def _normalized_entry(
        self,
        existing: dict[str, Any],
        category: SiteCategorySnapshot,
        all_existing: list[dict[str, Any]],
    ) -> dict[str, Any]:
        path = list(category.path)
        entry = dict(existing)
        entry["type"] = category.type.value
        entry["path"] = path
        entry["slug"] = path[-1]
        entry["label"] = str(existing.get("label") or category.label or path[-1])
        if "enabled" not in entry or entry.get("enabled") is None:
            entry["enabled"] = True
        if "sort_order" not in entry or entry.get("sort_order") is None:
            entry["sort_order"] = self.category_entries.next_sort_order(all_existing, category.type, len(path))
        return entry

    @staticmethod
    def _entry_label(entry: dict[str, Any]) -> str:
        label = str(entry.get("label") or "").strip()
        if label:
            return label
        path = [str(part).strip() for part in (entry.get("path") or []) if str(part).strip()]
        return "/".join(path) or str(entry.get("slug") or "未知分类")

    @staticmethod
    def _unified_diff(old: str, new: str, label: str) -> str:
        return "".join(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile=label,
                tofile=label,
            )
        )

    def _registry_content(self, entries: list[dict[str, Any]]) -> str:
        return yaml.safe_dump(
            {"categories": entries},
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )

    def _entry_key(self, entry: dict[str, Any]) -> str | None:
        article_type = str(entry.get("type") or ArticleType.docs.value)
        path = [str(part).strip() for part in (entry.get("path") or []) if str(part).strip()]
        if not path:
            slug = str(entry.get("slug") or "").strip()
            path = [slug] if slug else []
        if article_type not in {ArticleType.docs.value, ArticleType.blog.value} or not path:
            return None
        return f"{article_type}:{'/'.join(path)}"

    @staticmethod
    def _category_key(article_type: ArticleType, path: list[str]) -> str:
        return f"{article_type.value}:{'/'.join(path)}"
