"""Category registry YAML operations."""

from __future__ import annotations

from typing import Any

import yaml

from scr.core.config import settings
from scr.core.exceptions import BadRequestError


class CategoryRegistryService:
    """Read, write, snapshot, and restore ``categories.yml``."""

    def __init__(self) -> None:
        self.registry_path = settings.content_schema_dir / "categories.yml"

    def load_entries(self) -> list[dict[str, Any]]:
        """Read categories.yml, accepting both top-level lists and {categories: [...]}."""
        if not self.registry_path.exists():
            return []

        try:
            loaded = yaml.safe_load(self.registry_path.read_text(encoding="utf-8")) or []
        except yaml.YAMLError as exc:
            raise BadRequestError("分类注册表格式错误。", code="category_registry_invalid") from exc
        if isinstance(loaded, dict):
            loaded = loaded.get("categories", [])
        if not isinstance(loaded, list):
            raise BadRequestError("分类注册表格式错误。", code="category_registry_invalid")

        entries: list[dict[str, Any]] = []
        for item in loaded:
            if isinstance(item, dict):
                entries.append(dict(item))
        return entries

    def write_entries(self, entries: list[dict[str, Any]]) -> None:
        """Write categories.yml in the normalized {categories: [...]} format."""
        content = yaml.safe_dump(
            {"categories": entries},
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(content, encoding="utf-8")

    def snapshot(self) -> str | None:
        """Return raw categories.yml content, or None when it does not exist."""
        if not self.registry_path.exists():
            return None
        return self.registry_path.read_text(encoding="utf-8")

    def restore(self, snapshot: str | None) -> None:
        """Restore categories.yml from a previous snapshot."""
        if snapshot is None:
            if self.registry_path.exists():
                self.registry_path.unlink()
            return
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(snapshot, encoding="utf-8")
