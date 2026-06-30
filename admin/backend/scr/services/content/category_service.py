"""分类注册表服务。"""

import base64
from pathlib import Path
from typing import Any

import yaml

from scr.core.config import settings
from scr.core.exceptions import BadRequestError, NotFoundError
from scr.models.article import ArticleType
from scr.schemas.category import CategoryDTO, CategoryUpdateDTO
from scr.services.content.filesystem_service import FileSystemService
from scr.services.content.markdown_service import MarkdownService


class CategoryService:
    """维护内容分类树，兼容 schema 注册表与 docs 目录推导。"""

    def __init__(self) -> None:
        self.filesystem = FileSystemService()
        self.markdown = MarkdownService()
        self.registry_path = settings.content_schema_dir / "categories.yml"

    def type_label(self, article_type: ArticleType) -> str:
        """返回内容类型显示名。"""
        return "知识库" if article_type == ArticleType.docs else "博客"

    def resolve_article_category(
        self,
        article_type: ArticleType,
        category_path: list[str],
        candidates: list[str] | None = None,
    ) -> tuple[list[str], str]:
        """根据文章路径、Front Matter 或标签解析分类路径与显示名。"""
        categories = self._category_lookup()
        normalized_path = [part.strip() for part in category_path if part.strip()]
        if normalized_path:
            key = (article_type.value, tuple(normalized_path))
            category = categories.get(key)
            label = str(category.get("label")) if category else self._default_label(normalized_path[-1])
            return normalized_path, label

        candidate_values = [candidate.strip() for candidate in candidates or [] if candidate.strip()]
        for candidate in candidate_values:
            matched_path = self._match_category_path(article_type, candidate, categories)
            if matched_path:
                category = categories[(article_type.value, tuple(matched_path))]
                return matched_path, str(category["label"])

        return [], self.type_label(article_type)

    def list_categories(
        self,
        *,
        article_type: ArticleType | None = None,
        include_empty: bool = True,
        include_counts: bool = False,
    ) -> list[CategoryDTO]:
        """返回分类树；schema 不存在时从 docs 目录推导。"""
        entries = self._load_registry_entries()
        categories = self._derive_categories_from_docs()
        categories.update(self._categories_from_registry(entries))

        requested_types = [article_type] if article_type else [ArticleType.docs, ArticleType.blog]
        result: list[CategoryDTO] = []
        for current_type in requested_types:
            nodes = {
                path: category
                for path, category in categories.items()
                if category["type"] == current_type.value
            }
            counts = self._article_counts_by_category(current_type) if include_counts or not include_empty else {}
            result.extend(self._build_tree(current_type, nodes, counts, include_empty, include_counts))

        return result

    def update_category(self, category_id: str, payload: CategoryUpdateDTO) -> CategoryDTO:
        """更新分类注册表中的展示信息；不会移动真实目录。"""
        article_type, path = self._decode_category_id(category_id)
        if not path:
            raise BadRequestError("分类 ID 无效。", code="category_id_invalid")

        existing_paths = self._existing_category_paths(article_type)
        if tuple(path) not in existing_paths:
            raise NotFoundError("分类不存在。", code="category_not_found")

        entries = self._load_registry_entries()
        entry = self._find_or_create_entry(entries, article_type, path)
        if payload.label is not None:
            entry["label"] = payload.label
        if payload.description is not None:
            entry["description"] = payload.description
        if payload.cover is not None:
            entry["cover"] = payload.cover

        settings.content_schema_dir.mkdir(parents=True, exist_ok=True)
        self._write_registry_entries(entries)

        updated = self.list_categories(article_type=article_type, include_empty=True, include_counts=True)
        found = self._find_category_in_tree(updated, path)
        if not found:
            raise NotFoundError("分类不存在。", code="category_not_found")
        return found

    def ensure_category_path(self, article_type: ArticleType, path: list[str]) -> list[str]:
        """确保分类路径存在于目录与注册表中，返回每级分类显示名。"""
        normalized_path = [segment.strip() for segment in path if segment.strip()]
        if not normalized_path:
            return []

        if article_type == ArticleType.docs:
            target_dir = settings.docs_dir.joinpath(*normalized_path)
            target_dir.mkdir(parents=True, exist_ok=True)

        entries = self._load_registry_entries()
        labels: list[str] = []
        changed = False
        for index in range(1, len(normalized_path) + 1):
            current_path = normalized_path[:index]
            entry = self._find_or_create_entry(entries, article_type, current_path)
            if "sort_order" not in entry or entry.get("sort_order") is None:
                entry["sort_order"] = self._next_sort_order(entries, article_type, index)
                changed = True
            if "enabled" not in entry:
                entry["enabled"] = True
                changed = True
            labels.append(str(entry.get("label") or current_path[-1]))
            if entry.get("label") is None:
                entry["label"] = current_path[-1]
                changed = True

        if changed:
            settings.content_schema_dir.mkdir(parents=True, exist_ok=True)
            self._write_registry_entries(entries)

        return labels

    def _derive_categories_from_docs(self) -> dict[tuple[str, tuple[str, ...]], dict[str, Any]]:
        """从 site/docs 目录推导分类节点。"""
        categories: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
        docs_root = settings.docs_dir
        if not docs_root.exists():
            return categories

        for directory in sorted((path for path in docs_root.rglob("*") if path.is_dir()), key=lambda item: item.as_posix()):
            relative_path = directory.relative_to(docs_root).as_posix()
            parts = tuple(part for part in relative_path.split("/") if part)
            if not parts:
                continue
            categories[(ArticleType.docs.value, parts)] = {
                "type": ArticleType.docs.value,
                "slug": parts[-1],
                "label": self._default_label(parts[-1]),
                "path": list(parts),
                "description": None,
                "cover": None,
                "sort_order": None,
                "enabled": True,
            }
        return categories

    def _categories_from_registry(self, entries: list[dict[str, Any]]) -> dict[tuple[str, tuple[str, ...]], dict[str, Any]]:
        """将注册表条目转换为分类节点映射。"""
        categories: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
        for entry in entries:
            try:
                article_type = ArticleType(str(entry.get("type", ArticleType.docs.value)))
            except ValueError:
                continue

            path = self._entry_path(entry)
            if not path:
                continue

            categories[(article_type.value, tuple(path))] = {
                "type": article_type.value,
                "slug": path[-1],
                "label": str(entry.get("label") or self._default_label(path[-1])),
                "path": path,
                "aliases": self._list_value(entry.get("aliases")),
                "description": self._optional_string(entry.get("description")),
                "cover": self._optional_string(entry.get("cover")),
                "sort_order": self._optional_int(entry.get("sort_order")),
                "enabled": bool(entry.get("enabled", True)),
            }
        return categories

    def _build_tree(
        self,
        article_type: ArticleType,
        nodes: dict[tuple[str, tuple[str, ...]], dict[str, Any]],
        counts: dict[tuple[str, ...], int],
        include_empty: bool,
        include_counts: bool,
    ) -> list[CategoryDTO]:
        """把扁平分类节点组装为树。"""
        path_map: dict[tuple[str, ...], CategoryDTO] = {}
        for _, path in sorted(nodes.keys(), key=lambda item: self._category_sort_key(nodes[item], item[1])):
            node = nodes[(article_type.value, path)]
            if not node.get("enabled", True):
                continue
            count = counts.get(path, 0)
            path_map[path] = CategoryDTO(
                id=self._encode_category_id(article_type, list(path)),
                type=article_type,
                slug=node["slug"],
                label=node["label"],
                path=list(path),
                description=node.get("description"),
                cover=node.get("cover"),
                sort_order=node.get("sort_order"),
                enabled=bool(node.get("enabled", True)),
                article_count=count if include_counts else None,
                children=[],
            )

        roots: list[CategoryDTO] = []
        for path, category in path_map.items():
            parent_path = path[:-1]
            parent = path_map.get(parent_path)
            if parent:
                parent.children.append(category)
            else:
                roots.append(category)

        if include_empty:
            return roots
        return [category for category in roots if self._has_articles_by_count(category, counts)]

    def _article_counts_by_category(self, article_type: ArticleType) -> dict[tuple[str, ...], int]:
        """统计每个分类下的文章数量，计入其所有父分类。"""
        counts: dict[tuple[str, ...], int] = {}
        for path in self.filesystem.scan_article_files(article_type):
            relative_path = self.filesystem.relative_posix_path(article_type, path)
            if article_type == ArticleType.docs:
                parts = tuple(Path(relative_path).parent.as_posix().split("/"))
            else:
                parsed = self.markdown.parse(path.read_text(encoding="utf-8"))
                parts = tuple(self.resolve_article_category(article_type, [], self._frontmatter_category_candidates(parsed.frontmatter))[0])
            if parts == (".",) or not parts:
                continue
            for index in range(1, len(parts) + 1):
                category_path = parts[:index]
                counts[category_path] = counts.get(category_path, 0) + 1
        return counts

    def _existing_category_paths(self, article_type: ArticleType) -> set[tuple[str, ...]]:
        """返回当前存在的分类路径，包含目录推导和注册表条目。"""
        entries = self._load_registry_entries()
        categories = self._derive_categories_from_docs()
        categories.update(self._categories_from_registry(entries))
        return {
            path
            for type_value, path in categories
            if type_value == article_type.value
        }

    def _find_or_create_entry(
        self,
        entries: list[dict[str, Any]],
        article_type: ArticleType,
        path: list[str],
    ) -> dict[str, Any]:
        """查找注册表条目；不存在时追加一个新的覆盖条目。"""
        for entry in entries:
            if str(entry.get("type", ArticleType.docs.value)) == article_type.value and self._entry_path(entry) == path:
                return entry

        entry = {
            "type": article_type.value,
            "slug": path[-1],
            "path": path,
            "label": self._default_label(path[-1]),
            "description": None,
            "cover": None,
        }
        entries.append(entry)
        return entry

    def _next_sort_order(self, entries: list[dict[str, Any]], article_type: ArticleType, depth: int) -> int:
        """按同类型、同层级已有最大排序号递增。"""
        orders: list[int] = []
        for entry in entries:
            if str(entry.get("type", ArticleType.docs.value)) != article_type.value:
                continue
            if len(self._entry_path(entry)) != depth:
                continue
            sort_order = self._optional_int(entry.get("sort_order"))
            if sort_order is not None:
                orders.append(sort_order)
        return (max(orders) + 10) if orders else depth * 10

    def _load_registry_entries(self) -> list[dict[str, Any]]:
        """读取 categories.yml，兼容顶层列表和 {categories: [...]} 两种格式。"""
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

    def _write_registry_entries(self, entries: list[dict[str, Any]]) -> None:
        """写回 categories.yml。"""
        content = yaml.safe_dump(
            {"categories": entries},
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )
        self.registry_path.write_text(content, encoding="utf-8")

    def snapshot_registry(self) -> str | None:
        """返回当前 categories.yml 原始内容，供调用方在失败时回滚；文件不存在时返回 None。"""
        if not self.registry_path.exists():
            return None
        return self.registry_path.read_text(encoding="utf-8")

    def restore_registry(self, snapshot: str | None) -> None:
        """用快照恢复 categories.yml。

        snapshot 为 None 表示快照时文件尚不存在，恢复时删除本次新建的注册表文件；
        否则用快照内容覆盖，撤销 ensure_category_path 写入的条目。
        """
        if snapshot is None:
            if self.registry_path.exists():
                self.registry_path.unlink()
            return
        self.registry_path.write_text(snapshot, encoding="utf-8")

    def _category_lookup(self) -> dict[tuple[str, tuple[str, ...]], dict[str, Any]]:
        entries = self._load_registry_entries()
        categories = self._derive_categories_from_docs()
        categories.update(self._categories_from_registry(entries))
        return categories

    def _match_category_path(
        self,
        article_type: ArticleType,
        candidate: str,
        categories: dict[tuple[str, tuple[str, ...]], dict[str, Any]],
    ) -> list[str] | None:
        normalized = candidate.strip().lower()
        if not normalized:
            return None

        for (type_value, path), category in categories.items():
            if type_value != article_type.value:
                continue
            if not category.get("enabled", True):
                continue
            aliases = [str(alias) for alias in category.get("aliases", []) if str(alias).strip()]
            values = {
                str(category.get("slug", "")).lower(),
                str(category.get("label", "")).lower(),
                "/".join(path).lower(),
                *[alias.lower() for alias in aliases],
            }
            if normalized in values:
                return list(path)
        return None

    def _frontmatter_category_candidates(self, frontmatter: dict[str, Any]) -> list[str]:
        candidates: list[str] = []
        candidates.extend(self._list_value(frontmatter.get("category")))
        candidates.extend(self._list_value(frontmatter.get("categories")))
        candidates.extend(self._list_value(frontmatter.get("tags")))
        return candidates

    @staticmethod
    def _entry_path(entry: dict[str, Any]) -> list[str]:
        """解析注册表条目中的分类路径。"""
        raw_path = entry.get("path")
        if isinstance(raw_path, list):
            return [str(part).strip() for part in raw_path if str(part).strip()]

        slug = str(entry.get("slug") or "").strip()
        parent_path = entry.get("parent_path") or []
        if not slug or not isinstance(parent_path, list):
            return [slug] if slug else []
        return [*[str(part).strip() for part in parent_path if str(part).strip()], slug]

    @staticmethod
    def _list_value(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return [str(value).strip()] if str(value).strip() else []

    @staticmethod
    def _default_label(slug: str) -> str:
        """没有注册表覆盖时，以 slug 生成一个可读 label。"""
        return slug.replace("-", " ").title()

    @staticmethod
    def _optional_string(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _optional_int(value: object) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _category_sort_key(node: dict[str, Any], path: tuple[str, ...]) -> tuple[int, int, str]:
        sort_order = node.get("sort_order")
        order = sort_order if isinstance(sort_order, int) else 9999
        return (order, len(path), "/".join(path))

    @staticmethod
    def _has_articles_by_count(category: CategoryDTO, counts: dict[tuple[str, ...], int]) -> bool:
        return bool(counts.get(tuple(category.path))) or any(
            CategoryService._has_articles_by_count(child, counts) for child in category.children
        )

    @staticmethod
    def _find_category_in_tree(categories: list[CategoryDTO], path: list[str]) -> CategoryDTO | None:
        for category in categories:
            if category.path == path:
                return category
            found = CategoryService._find_category_in_tree(category.children, path)
            if found:
                return found
        return None

    @staticmethod
    def _encode_category_id(article_type: ArticleType, path: list[str]) -> str:
        raw = f"{article_type.value}:{'/'.join(path)}"
        return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")

    @staticmethod
    def _decode_category_id(category_id: str) -> tuple[ArticleType, list[str]]:
        padding = "=" * (-len(category_id) % 4)
        try:
            raw = base64.urlsafe_b64decode(f"{category_id}{padding}").decode("utf-8")
            type_text, path_text = raw.split(":", 1)
            article_type = ArticleType(type_text)
        except (ValueError, UnicodeDecodeError) as exc:
            raise BadRequestError("分类 ID 无效。", code="category_id_invalid") from exc

        path = [part for part in path_text.split("/") if part]
        return article_type, path
