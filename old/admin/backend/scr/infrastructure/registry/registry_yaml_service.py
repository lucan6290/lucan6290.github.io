"""Registry YAML management service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from scr.core.config import settings
from scr.core.exceptions import BadRequestError
from scr.models.article import ArticleType
from scr.schemas.registry_index import (
    RegistryIndexSyncResultDTO,
    RegistryYamlEntriesDTO,
    RegistryYamlEntriesSaveDTO,
    RegistryYamlFileDTO,
    RegistryYamlSaveDTO,
)
from scr.services.content.categories.category_registry_service import CategoryRegistryService
from scr.services.content.categories.category_index_service import CategoryIndexService
from scr.infrastructure.registry.tag_registry_service import TagRegistryService


class RegistryYamlService:
    """Read and write categories/tags YAML registries."""

    registry_top_keys = {
        "categories": "categories",
        "tags": "tags",
    }

    def __init__(self) -> None:
        self.category_registry = CategoryRegistryService()
        self.tag_registry = TagRegistryService()

    def get_yaml_file(self, registry_type: str) -> RegistryYamlFileDTO:
        """Read raw YAML registry content."""
        path = self._registry_path(registry_type)
        return RegistryYamlFileDTO(
            registry_type=registry_type,
            path=self._relative_path(path),
            exists=path.exists(),
            content=path.read_text(encoding="utf-8") if path.exists() else self._empty_registry_content(registry_type),
        )

    def save_yaml_file(
        self,
        registry_type: str,
        payload: RegistryYamlSaveDTO,
        *,
        rebuild,
    ) -> RegistryIndexSyncResultDTO | RegistryYamlFileDTO:
        """Save raw YAML content after parsing and validating it."""
        self.parse_registry_content(registry_type, payload.content)
        path = self._registry_path(registry_type)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload.content, encoding="utf-8")
        if payload.rebuild_index:
            return rebuild()
        return self.get_yaml_file(registry_type)

    def get_yaml_entries(self, registry_type: str) -> RegistryYamlEntriesDTO:
        """Read normalized YAML registry entries."""
        registry = self._registry_adapter(registry_type)
        path = registry.registry_path
        return RegistryYamlEntriesDTO(
            registry_type=registry_type,
            path=self._relative_path(path),
            exists=path.exists(),
            items=registry.load_entries(),
        )

    def save_yaml_entries(
        self,
        registry_type: str,
        payload: RegistryYamlEntriesSaveDTO,
        *,
        rebuild,
    ) -> RegistryIndexSyncResultDTO | RegistryYamlEntriesDTO:
        """Save normalized YAML registry entries."""
        normalized = self.normalize_registry_type(registry_type)
        self.validate_registry_entries(normalized, payload.items)
        self._registry_adapter(normalized).write_entries(payload.items)
        if payload.rebuild_index:
            return rebuild()
        return self.get_yaml_entries(registry_type)

    def normalize_registry_type(self, registry_type: str) -> str:
        aliases = {
            "category": "categories",
            "categories": "categories",
            "tag": "tags",
            "tags": "tags",
        }
        normalized = aliases.get(registry_type.strip().lower())
        if not normalized:
            raise BadRequestError("注册表类型不支持。", code="invalid_registry_type", details={"registry_type": registry_type})
        return normalized

    def parse_registry_content(self, registry_type: str, content: str) -> list[dict[str, Any]]:
        normalized = self.normalize_registry_type(registry_type)
        try:
            loaded = yaml.safe_load(content) or {}
        except yaml.YAMLError as exc:
            raise BadRequestError("YAML 注册表格式错误。", code="registry_yaml_invalid") from exc

        if isinstance(loaded, list):
            raw_items = loaded
        elif isinstance(loaded, dict):
            raw_items = loaded.get(self.registry_top_keys[normalized], [])
        else:
            raise BadRequestError("YAML 注册表格式错误。", code="registry_yaml_invalid")

        if not isinstance(raw_items, list):
            raise BadRequestError("YAML 注册表条目必须是列表。", code="registry_yaml_invalid")

        items: list[dict[str, Any]] = []
        for item in raw_items:
            if not isinstance(item, dict):
                raise BadRequestError("YAML 注册表条目必须是对象。", code="registry_yaml_invalid")
            items.append(dict(item))
        self.validate_registry_entries(normalized, items)
        return items

    def validate_registry_entries(self, registry_type: str, items: list[dict[str, Any]]) -> None:
        normalized = self.normalize_registry_type(registry_type)
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise BadRequestError("YAML 注册表条目必须是对象。", code="registry_yaml_invalid", details={"index": index})
            if normalized == "categories" and not self.registry_entry_key(normalized, item):
                raise BadRequestError("分类条目必须包含 type 与 path/slug。", code="registry_yaml_invalid", details={"index": index})
            if normalized == "tags" and not str(item.get("slug") or "").strip():
                raise BadRequestError("标签条目必须包含 slug。", code="registry_yaml_invalid", details={"index": index})

    def registry_entry_key(self, registry_type: str, entry: dict[str, Any]) -> str | None:
        normalized = self.normalize_registry_type(registry_type)
        if normalized == "categories":
            article_type = str(entry.get("type") or ArticleType.docs.value).strip()
            path = CategoryIndexService._entry_path(entry)
            return f"{article_type}:{'/'.join(path)}" if article_type and path else None
        if normalized == "tags":
            slug = str(entry.get("slug") or "").strip()
            return slug or None
        return None

    def _registry_path(self, registry_type: str) -> Path:
        return self._registry_adapter(registry_type).registry_path

    def _registry_adapter(self, registry_type: str) -> CategoryRegistryService | TagRegistryService:
        normalized = self.normalize_registry_type(registry_type)
        if normalized == "categories":
            return self.category_registry
        return self.tag_registry

    def _empty_registry_content(self, registry_type: str) -> str:
        normalized = self.normalize_registry_type(registry_type)
        return yaml.safe_dump(
            {self.registry_top_keys[normalized]: []},
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )

    @staticmethod
    def _relative_path(path: Path) -> str:
        try:
            return path.resolve().relative_to(settings.project_root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()
