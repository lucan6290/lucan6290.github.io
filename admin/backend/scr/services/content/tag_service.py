"""标签注册表服务。"""

import hashlib
import re
from typing import Any

import yaml

from scr.core.config import settings
from scr.core.exceptions import BadRequestError, ConflictError
from scr.models.article import ArticleType
from scr.schemas.tag import TagCreateDTO, TagDTO, TagSyncResultDTO
from scr.services.content.filesystem_service import FileSystemService
from scr.services.content.markdown_service import MarkdownService


class TagService:
    """维护标签列表，合并注册表与文章 Front Matter 使用情况。"""

    slug_pattern = re.compile(r"^[a-z0-9][a-z0-9-]*$")

    def __init__(self) -> None:
        self.filesystem = FileSystemService()
        self.markdown = MarkdownService()
        self.registry_path = settings.content_schema_dir / "tags.yml"

    def list_tags(
        self,
        *,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 100,
        sort: str = "label",
    ) -> list[TagDTO]:
        """返回标签列表，包含注册表标签与文章中实际出现的标签。"""
        usage = self._tag_usage()
        registry_entries = self._load_registry_entries()
        tags_by_slug: dict[str, TagDTO] = {}

        for entry in registry_entries:
            slug = str(entry.get("slug") or "").strip()
            if not slug:
                continue
            tags_by_slug[slug] = TagDTO(
                slug=slug,
                label=str(entry.get("label") or slug),
                description=self._optional_string(entry.get("description")),
                usage_count=usage.get(slug, 0),
            )

        for slug, count in usage.items():
            if slug not in tags_by_slug:
                tags_by_slug[slug] = TagDTO(
                    slug=slug,
                    label=self._label_from_slug(slug),
                    usage_count=count,
                )

        tags = list(tags_by_slug.values())
        tags = self._filter_tags(tags, keyword)
        tags = self._sort_tags(tags, sort)
        start = (page - 1) * page_size
        return tags[start : start + page_size]

    def sync_tags(self, *, dry_run: bool = True, confirm: bool = False) -> TagSyncResultDTO:
        """将文章中出现但未注册的标签写入 admin/backend/data/content-schema/tags.yml。"""
        usage = self._tag_usage()
        entries = self._load_registry_entries()
        registered_slugs = {
            str(entry.get("slug") or "").strip()
            for entry in entries
            if str(entry.get("slug") or "").strip()
        }

        created_tags = [
            TagDTO(slug=slug, label=self._label_from_slug(slug), usage_count=usage[slug])
            for slug in sorted(usage)
            if slug not in registered_slugs
        ]

        if not dry_run and not confirm:
            raise BadRequestError("同步标签需要显式确认。", code="confirmation_required")

        if not dry_run and created_tags:
            settings.content_schema_dir.mkdir(parents=True, exist_ok=True)
            for tag in created_tags:
                entries.append(
                    {
                        "slug": tag.slug,
                        "label": tag.label,
                        "description": tag.description,
                    }
                )
            self._write_registry_entries(entries)

        return TagSyncResultDTO(
            dry_run=dry_run,
            requires_confirmation=dry_run,
            discovered_count=len(usage),
            existing_count=len(registered_slugs & set(usage)),
            created_tags=created_tags,
            warnings=[],
        )

    def create_tag(self, payload: TagCreateDTO) -> TagDTO:
        """创建单个标签并写入注册表。"""
        label = payload.label.strip()
        slug = (payload.slug.strip() if payload.slug else self._slug_from_label(label))
        if not self.slug_pattern.fullmatch(slug):
            raise BadRequestError("标签 slug 不合法。", code="invalid_slug", details={"slug": slug})

        entries = self._load_registry_entries()
        if any(str(entry.get("slug") or "").strip() == slug for entry in entries):
            raise ConflictError("标签已存在。", code="tag_already_exists", details={"slug": slug})

        entry = {
            "slug": slug,
            "label": label,
            "description": self._optional_string(payload.description),
        }
        entries.append(entry)
        settings.content_schema_dir.mkdir(parents=True, exist_ok=True)
        self._write_registry_entries(entries)
        return TagDTO(slug=slug, label=label, description=entry["description"], usage_count=0)

    def ensure_tags(self, labels: list[str]) -> list[TagDTO]:
        """确保给定标签写入注册表，返回对应标签 DTO。"""
        normalized_labels = [label.strip() for label in labels if label.strip()]
        if not normalized_labels:
            return []

        entries = self._load_registry_entries()
        registered = {
            str(entry.get("slug") or "").strip(): entry
            for entry in entries
            if str(entry.get("slug") or "").strip()
        }
        result: list[TagDTO] = []
        changed = False

        for label in normalized_labels:
            slug = self._slug_from_label(label)
            entry = registered.get(slug)
            if entry is None:
                entry = {
                    "slug": slug,
                    "label": label,
                    "description": None,
                }
                entries.append(entry)
                registered[slug] = entry
                changed = True
            elif not str(entry.get("label") or "").strip():
                entry["label"] = label
                changed = True

            result.append(
                TagDTO(
                    slug=slug,
                    label=str(entry.get("label") or label),
                    description=self._optional_string(entry.get("description")),
                    usage_count=0,
                )
            )

        if changed:
            settings.content_schema_dir.mkdir(parents=True, exist_ok=True)
            self._write_registry_entries(entries)

        return result

    def _tag_usage(self) -> dict[str, int]:
        """统计所有文章 Front Matter 中的 tags 使用次数。"""
        labels_by_slug: dict[str, str] = {}
        usage: dict[str, int] = {}

        for article_type in [ArticleType.docs, ArticleType.blog]:
            for path in self.filesystem.scan_article_files(article_type):
                parsed = self.markdown.parse(path.read_text(encoding="utf-8"))
                for label in self._list_value(parsed.frontmatter.get("tags")):
                    slug = self._slug_from_label(label)
                    labels_by_slug.setdefault(slug, label)
                    usage[slug] = usage.get(slug, 0) + 1

        self._labels_by_slug = labels_by_slug
        return usage

    def _load_registry_entries(self) -> list[dict[str, Any]]:
        """读取 tags.yml，兼容顶层列表和 {tags: [...]} 两种格式。"""
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

    def _write_registry_entries(self, entries: list[dict[str, Any]]) -> None:
        """写回 tags.yml。"""
        content = yaml.safe_dump(
            {"tags": entries},
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )
        self.registry_path.write_text(content, encoding="utf-8")

    def _label_from_slug(self, slug: str) -> str:
        """优先使用文章中出现过的原始标签文本作为显示名。"""
        labels = getattr(self, "_labels_by_slug", {})
        if slug in labels:
            return labels[slug]
        return slug.replace("-", " ").title()

    def _slug_from_label(self, label: str) -> str:
        """将标签文本转为安全 slug；中文等文本使用稳定哈希兜底。"""
        normalized = label.strip()
        slug = normalized.lower()
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"[^a-z0-9-]", "-", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")
        if slug and self.slug_pattern.fullmatch(slug):
            return slug

        digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:10]
        return f"tag-{digest}"

    @staticmethod
    def _filter_tags(tags: list[TagDTO], keyword: str | None) -> list[TagDTO]:
        if not keyword:
            return tags
        normalized = keyword.lower()
        return [
            tag
            for tag in tags
            if normalized in tag.slug.lower()
            or normalized in tag.label.lower()
            or normalized in (tag.description or "").lower()
        ]

    @staticmethod
    def _sort_tags(tags: list[TagDTO], sort: str) -> list[TagDTO]:
        descending = sort.startswith("-")
        field_name = sort[1:] if descending else sort
        if field_name not in {"label", "slug", "usage_count"}:
            raise BadRequestError("sort 字段不支持。", code="invalid_sort_field", details={"sort": sort})

        return sorted(
            tags,
            key=lambda tag: getattr(tag, field_name),
            reverse=descending,
        )

    @staticmethod
    def _list_value(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return [str(value).strip()] if str(value).strip() else []

    @staticmethod
    def _optional_string(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
