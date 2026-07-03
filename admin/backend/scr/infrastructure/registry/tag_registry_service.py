"""Tag registry YAML operations."""

from __future__ import annotations

from typing import Any

import yaml

from scr.core.config import settings
from scr.core.exceptions import BadRequestError


class TagRegistryService:
    """Read and write ``tags.yml``."""

    def __init__(self) -> None:
        self.registry_path = settings.content_schema_dir / "tags.yml"

    def load_entries(self) -> list[dict[str, Any]]:
        """Read tags.yml, accepting both top-level lists and {tags: [...]}."""
        if not self.registry_path.exists():
            return []

        try:
            loaded = yaml.safe_load(self.registry_path.read_text(encoding="utf-8")) or []
        except yaml.YAMLError as exc:
            raise BadRequestError("标签注册表格式错误。", code="tag_registry_invalid") from exc
        if isinstance(loaded, dict):
            loaded = loaded.get("tags", [])
        if not isinstance(loaded, list):
            raise BadRequestError("标签注册表格式错误。", code="tag_registry_invalid")

        entries: list[dict[str, Any]] = []
        for item in loaded:
            if isinstance(item, dict):
                entries.append(dict(item))
        return entries

    def write_entries(self, entries: list[dict[str, Any]]) -> None:
        """Write tags.yml in the normalized {tags: [...]} format."""
        content = yaml.safe_dump(
            {"tags": entries},
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(content, encoding="utf-8")
