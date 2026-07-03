"""分类查询与分类树构建服务。"""

from pathlib import Path
from typing import Any

from scr.core.config import settings
from scr.models.article import ArticleType
from scr.schemas.category import CategoryDTO
from scr.services.content.categories.category_id_service import CategoryIdService
from scr.services.content.categories.category_registry_service import CategoryRegistryService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService


CategoryNodeMap = dict[tuple[str, tuple[str, ...]], dict[str, Any]]


class CategoryQueryService:
    """读取分类来源并组装管理端分类树。"""

    def __init__(self) -> None:
        self.filesystem = FileSystemService()
        self.registry = CategoryRegistryService()

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
        categories = self.category_lookup()
        normalized_path = [part.strip() for part in category_path if part.strip()]
        if normalized_path:
            key = (article_type.value, tuple(normalized_path))
            category = categories.get(key)
            label = str(category.get("label")) if category else self.default_label(normalized_path[-1])
            return normalized_path, label

        candidate_values = [candidate.strip() for candidate in candidates or [] if candidate.strip()]
        for candidate in candidate_values:
            matched_path = self.match_category_path(article_type, candidate, categories)
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
        """返回分类树；schema 不存在时从 docs/blog 目录推导。"""
        entries = self.load_registry_entries()
        categories = self.derive_categories_from_docs()
        categories.update(self.derive_categories_from_blog())
        categories.update(self.categories_from_registry(entries))

        requested_types = [article_type] if article_type else [ArticleType.docs, ArticleType.blog]
        result: list[CategoryDTO] = []
        for current_type in requested_types:
            nodes = {
                path: category
                for path, category in categories.items()
                if category["type"] == current_type.value
            }
            counts = self.article_counts_by_category(current_type) if include_counts or not include_empty else {}
            result.extend(self.build_tree(current_type, nodes, counts, include_empty, include_counts))

        return result

    def existing_category_paths(self, article_type: ArticleType) -> set[tuple[str, ...]]:
        """返回当前存在的分类路径，包含目录推导和注册表条目。"""
        entries = self.load_registry_entries()
        categories = self.derive_categories_from_docs()
        categories.update(self.derive_categories_from_blog())
        categories.update(self.categories_from_registry(entries))
        return {
            path
            for type_value, path in categories
            if type_value == article_type.value
        }

    def category_path_exists(self, article_type: ArticleType, path: list[str]) -> bool:
        """判断指定分类路径是否已存在。"""
        normalized_path = tuple(segment.strip() for segment in path if segment.strip())
        if not normalized_path:
            return True
        return normalized_path in self.existing_category_paths(article_type)

    def category_lookup(self) -> CategoryNodeMap:
        """返回按类型与路径索引的分类节点。"""
        entries = self.load_registry_entries()
        categories = self.derive_categories_from_docs()
        categories.update(self.derive_categories_from_blog())
        categories.update(self.categories_from_registry(entries))
        return categories

    def load_registry_entries(self) -> list[dict[str, Any]]:
        """读取 categories.yml，兼容顶层列表和 {categories: [...]} 两种格式。"""
        return self.registry.load_entries()

    def derive_categories_from_docs(self) -> CategoryNodeMap:
        """从 site/docs 目录推导分类节点。"""
        categories: CategoryNodeMap = {}
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
                "label": self.default_label(parts[-1]),
                "path": list(parts),
                "description": None,
                "cover": None,
                "sort_order": None,
                "enabled": True,
            }
        return categories

    def derive_categories_from_blog(self) -> CategoryNodeMap:
        """从 site/blog 一级目录推导 blog 分类节点。"""
        categories: CategoryNodeMap = {}
        blog_root = settings.blog_dir
        if not blog_root.exists():
            return categories

        for directory in sorted((path for path in blog_root.iterdir() if path.is_dir()), key=lambda item: item.as_posix()):
            slug = directory.name
            parts = (slug,)
            categories[(ArticleType.blog.value, parts)] = {
                "type": ArticleType.blog.value,
                "slug": slug,
                "label": self.default_label(slug),
                "path": list(parts),
                "description": None,
                "cover": None,
                "sort_order": None,
                "enabled": True,
            }
        return categories

    def categories_from_registry(self, entries: list[dict[str, Any]]) -> CategoryNodeMap:
        """将注册表条目转换为分类节点映射。"""
        categories: CategoryNodeMap = {}
        for entry in entries:
            try:
                article_type = ArticleType(str(entry.get("type", ArticleType.docs.value)))
            except ValueError:
                continue

            path = self.entry_path(entry)
            if not path:
                continue

            categories[(article_type.value, tuple(path))] = {
                "type": article_type.value,
                "slug": path[-1],
                "label": str(entry.get("label") or self.default_label(path[-1])),
                "path": path,
                "aliases": self.list_value(entry.get("aliases")),
                "description": self.optional_string(entry.get("description")),
                "cover": self.optional_string(entry.get("cover")),
                "sort_order": self.optional_int(entry.get("sort_order")),
                "enabled": bool(entry.get("enabled", True)),
            }
        return categories

    def build_tree(
        self,
        article_type: ArticleType,
        nodes: CategoryNodeMap,
        counts: dict[tuple[str, ...], int],
        include_empty: bool,
        include_counts: bool,
    ) -> list[CategoryDTO]:
        """把扁平分类节点组装为树。"""
        path_map: dict[tuple[str, ...], CategoryDTO] = {}
        for _, path in sorted(nodes.keys(), key=lambda item: self.category_sort_key(nodes[item], item[1])):
            node = nodes[(article_type.value, path)]
            if not node.get("enabled", True):
                continue
            count = counts.get(path, 0)
            path_map[path] = CategoryDTO(
                id=CategoryIdService.encode(article_type, list(path)),
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
        return [category for category in roots if self.has_articles_by_count(category, counts)]

    def article_counts_by_category(self, article_type: ArticleType) -> dict[tuple[str, ...], int]:
        """统计每个分类下的文章数量，计入其所有父分类。"""
        counts: dict[tuple[str, ...], int] = {}
        for path in self.filesystem.scan_article_files(article_type):
            relative_path = self.filesystem.relative_posix_path(article_type, path)
            if article_type == ArticleType.docs:
                parts = tuple(Path(relative_path).parent.as_posix().split("/"))
            else:
                parts = tuple(part for part in Path(relative_path).parent.as_posix().split("/")[:1] if part and part != ".")
            if parts == (".",) or not parts:
                continue
            for index in range(1, len(parts) + 1):
                category_path = parts[:index]
                counts[category_path] = counts.get(category_path, 0) + 1
        return counts

    def match_category_path(
        self,
        article_type: ArticleType,
        candidate: str,
        categories: CategoryNodeMap,
    ) -> list[str] | None:
        """按 slug、label、完整路径和 aliases 匹配分类路径。"""
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

    @classmethod
    def frontmatter_category_candidates(cls, frontmatter: dict[str, Any]) -> list[str]:
        """从文章 Front Matter 中提取可用于分类匹配的候选值。"""
        candidates: list[str] = []
        candidates.extend(cls.list_value(frontmatter.get("category")))
        candidates.extend(cls.list_value(frontmatter.get("categories")))
        candidates.extend(cls.list_value(frontmatter.get("tags")))
        return candidates

    @staticmethod
    def entry_path(entry: dict[str, Any]) -> list[str]:
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
    def list_value(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return [str(value).strip()] if str(value).strip() else []

    @staticmethod
    def default_label(slug: str) -> str:
        """没有注册表覆盖时，以 slug 生成一个可读 label。"""
        label = slug.replace("-", " ")
        if any(ord(char) > 127 for char in label):
            return label
        return label.title()

    @staticmethod
    def optional_string(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def optional_int(value: object) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def category_sort_key(node: dict[str, Any], path: tuple[str, ...]) -> tuple[int, int, str]:
        sort_order = node.get("sort_order")
        order = sort_order if isinstance(sort_order, int) else 9999
        return (order, len(path), "/".join(path))

    @classmethod
    def has_articles_by_count(cls, category: CategoryDTO, counts: dict[tuple[str, ...], int]) -> bool:
        return bool(counts.get(tuple(category.path))) or any(
            cls.has_articles_by_count(child, counts) for child in category.children
        )

    @classmethod
    def find_category_in_tree(cls, categories: list[CategoryDTO], path: list[str]) -> CategoryDTO | None:
        for category in categories:
            if category.path == path:
                return category
            found = cls.find_category_in_tree(category.children, path)
            if found:
                return found
        return None
