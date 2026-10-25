"""Synchronize Docusaurus site config files from actual content."""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field, replace
from pathlib import Path

from scr.core.config import settings
from scr.core.exceptions import BadRequestError
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.models.article import ArticleType
from scr.schemas.common import FileChangeDTO, MutationPlanDTO
from scr.services.content.categories.category_query_service import CategoryQueryService
from scr.services.content.categories.category_registry_service import CategoryRegistryService
from scr.services.content.docusaurus.docusaurus_config_service import DocusaurusConfigService
from scr.services.content.sidebars.blog_sidebar_service import BlogSidebarDocItem, BlogSidebarItem, BlogSidebarService
from scr.services.content.sidebars.sidebar_parser_service import SidebarParserService
from scr.services.content.sync.site_content_scanner import SiteArticleSnapshot, SiteCategorySnapshot, SiteContentScanner


@dataclass
class DocsSidebarNode:
    """Tree node for rendering ``sidebars.ts``."""

    path: tuple[str, ...]
    label: str
    has_index: bool = False
    articles: list[SiteArticleSnapshot] = field(default_factory=list)
    children: dict[str, "DocsSidebarNode"] = field(default_factory=dict)


class SiteConfigSyncService:
    """Update ``sidebars.ts``, ``blogSidebars.ts`` and ``docusaurus.config.ts``."""

    def __init__(self) -> None:
        self.scanner = SiteContentScanner()
        self.filesystem = FileSystemService()
        self.blog_sidebar = BlogSidebarService()
        self.docusaurus_config = DocusaurusConfigService()
        self.category_registry = CategoryRegistryService()
        self.sidebar_parser = SidebarParserService()

    def sync(self, *, dry_run: bool = True, confirm: bool = False) -> MutationPlanDTO:
        """Synchronize Docusaurus site config from real docs/blog content."""
        if not dry_run and not confirm:
            raise BadRequestError("同步 site 配置需要显式确认。", code="confirmation_required")

        snapshot = self.scanner.scan()
        sort_order_map = self._registry_sort_orders()
        article_order = self._existing_article_order()
        docs_categories = self._resolve_labels(snapshot.docs_categories)
        blog_categories = self._resolve_labels(snapshot.blog_categories)
        next_sidebars = self._render_docs_sidebars(docs_categories, snapshot.docs_articles, sort_order_map, article_order)
        next_blog_sidebars = self.blog_sidebar.render_categories(
            self._blog_sidebar_items(blog_categories, snapshot.blog_articles)
        )
        next_config = self.docusaurus_config.render_navbar_dropdowns(
            docs_items=self._docs_nav_items(docs_categories, sort_order_map),
            blog_items=self._blog_nav_items(blog_categories),
        )

        planned_files = [
            (settings.sidebars_path, next_sidebars, "同步 site/sidebars.ts"),
            (settings.blog_sidebars_path, next_blog_sidebars, "同步 site/blogSidebars.ts"),
            (settings.docusaurus_config_path, next_config, "同步 site/docusaurus.config.ts 的知识库/博客导航"),
        ]
        changes = [
            FileChangeDTO(
                action="update" if path.exists() else "create",
                target=self.filesystem.project_relative_posix_path(path),
                description=description if dry_run else description.replace("同步", "已同步", 1),
            )
            for path, content, description in planned_files
            if self._current_content(path) != content
        ]

        plan = MutationPlanDTO(
            dry_run=dry_run,
            requires_confirmation=dry_run,
            changes=changes,
            warnings=[],
            diff=self._render_diff(planned_files),
        )
        if dry_run:
            return plan

        for path, content, _description in planned_files:
            path.parent.mkdir(parents=True, exist_ok=True)
            if self._current_content(path) != content:
                path.write_text(content, encoding="utf-8")
        return plan

    def _resolve_labels(self, categories: tuple[SiteCategorySnapshot, ...]) -> tuple[SiteCategorySnapshot, ...]:
        """label 优先取 index.md title，其次保留注册表现有 label，最后回退目录名。"""
        registry_labels = self._registry_labels()
        resolved: list[SiteCategorySnapshot] = []
        for category in categories:
            if category.has_title:
                resolved.append(category)
                continue
            existing = registry_labels.get((category.type.value, category.path))
            if existing:
                resolved.append(replace(category, label=existing))
            else:
                resolved.append(category)
        return tuple(resolved)

    def _registry_labels(self) -> dict[tuple[str, tuple[str, ...]], str]:
        """读取 categories.yml 现有 label，作为「保留现有 label」的来源。"""
        labels: dict[tuple[str, tuple[str, ...]], str] = {}
        for entry in self.category_registry.load_entries():
            try:
                article_type = ArticleType(str(entry.get("type", ArticleType.docs.value)))
            except ValueError:
                continue
            path = CategoryQueryService.entry_path(entry)
            label = str(entry.get("label") or "").strip()
            if path and label:
                labels[(article_type.value, tuple(path))] = label
        return labels

    def _registry_sort_orders(self) -> dict[tuple[str, tuple[str, ...]], int]:
        """读取 categories.yml 的 sort_order，作为分类排序的依据（保留现有手写顺序）。"""
        sort_orders: dict[tuple[str, tuple[str, ...]], int] = {}
        for entry in self.category_registry.load_entries():
            try:
                article_type = ArticleType(str(entry.get("type", ArticleType.docs.value)))
            except ValueError:
                continue
            path = CategoryQueryService.entry_path(entry)
            sort_order = entry.get("sort_order")
            if path and isinstance(sort_order, int):
                sort_orders[(article_type.value, tuple(path))] = sort_order
        return sort_orders

    def _existing_article_order(self) -> dict[str, int]:
        """读取现有 sidebars.ts 中 doc_id 的出现顺序，用于保留文章顺序。"""
        if not settings.sidebars_path.exists():
            return {}
        content = settings.sidebars_path.read_text(encoding="utf-8")
        return {
            doc_id: index
            for index, doc_id in enumerate(self.sidebar_parser.registered_doc_ids_from_content(content))
        }

    @staticmethod
    def _sort_key_for_path(
        path: tuple[str, ...],
        sort_order_map: dict[tuple[str, tuple[str, ...]], int],
    ) -> tuple[int, str]:
        return (sort_order_map.get((ArticleType.docs.value, path), 1 << 30), "/".join(path))

    def _sorted_children(
        self,
        children: dict[str, DocsSidebarNode],
        sort_order_map: dict[tuple[str, tuple[str, ...]], int],
    ) -> list[DocsSidebarNode]:
        return sorted(children.values(), key=lambda node: self._sort_key_for_path(node.path, sort_order_map))

    @staticmethod
    def _sorted_articles(
        articles: list[SiteArticleSnapshot],
        article_order: dict[str, int],
    ) -> list[SiteArticleSnapshot]:
        return sorted(articles, key=lambda article: (article_order.get(article.doc_id, 1 << 30), article.doc_id))

    def _render_diff(self, planned_files: list[tuple[Path, str, str]]) -> str | None:
        parts: list[str] = []
        for path, content, _description in planned_files:
            current = self._current_content(path)
            if current == content:
                continue
            parts.append(self._unified_diff(current, content, self.filesystem.project_relative_posix_path(path)))
        return "\n".join(parts) if parts else None

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

    def _render_docs_sidebars(
        self,
        categories: tuple[SiteCategorySnapshot, ...],
        articles: tuple[SiteArticleSnapshot, ...],
        sort_order_map: dict[tuple[str, tuple[str, ...]], int],
        article_order: dict[str, int],
    ) -> str:
        category_by_path = {category.path: category for category in categories}
        roots: dict[str, DocsSidebarNode] = {}
        root_docs = sorted(
            [article for article in articles if not article.category_path and not article.is_index],
            key=lambda item: item.doc_id,
        )
        has_docs_home = any(article.relative_path.lower() in {"index.md", "index.mdx"} for article in articles)

        for category in categories:
            if not category.path:
                continue
            current_children = roots
            parent: DocsSidebarNode | None = None
            for depth in range(1, len(category.path) + 1):
                current_path = category.path[:depth]
                current_category = category_by_path.get(current_path)
                node = current_children.get(current_path[-1])
                if node is None:
                    node = DocsSidebarNode(
                        path=current_path,
                        label=(current_category.label if current_category else current_path[-1]),
                        has_index=bool(current_category and current_category.has_index),
                    )
                    current_children[current_path[-1]] = node
                elif current_category:
                    node.label = current_category.label
                    node.has_index = current_category.has_index
                parent = node
                current_children = node.children
            _ = parent

        for article in articles:
            if article.is_index or not article.category_path:
                continue
            node = self._find_node(roots, article.category_path)
            if node is not None:
                node.articles.append(article)

        lines = [
            "import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';",
            "",
            "const sidebars: SidebarsConfig = {",
        ]
        overview_items = ["index"] if has_docs_home else [article.doc_id for article in root_docs]
        if overview_items:
            lines.extend(["  overviewSidebar: ["])
            for doc_id in overview_items:
                lines.append(f"    '{self._ts_single_quoted(doc_id)}',")
            lines.extend(["  ],", ""])

        for key, node in sorted(roots.items(), key=lambda item: item[0]):
            lines.append(f"  '{self._ts_single_quoted(key)}Sidebar': [")
            self._render_docs_node(lines, node, 2, sort_order_map, article_order)
            lines.extend(["  ],", ""])

        lines.extend(["};", "", "export default sidebars;", ""])
        return "\n".join(lines)

    def _render_docs_node(
        self,
        lines: list[str],
        node: DocsSidebarNode,
        indent_level: int,
        sort_order_map: dict[tuple[str, tuple[str, ...]], int],
        article_order: dict[str, int],
    ) -> None:
        indent = "  " * indent_level
        lines.extend(
            [
                f"{indent}{{",
                f"{indent}  type: 'category',",
                f"{indent}  label: '{self._ts_single_quoted(node.label)}',",
                f"{indent}  collapsed: false,",
            ]
        )
        if node.has_index:
            lines.extend(
                [
                    f"{indent}  link: {{",
                    f"{indent}    type: 'doc',",
                    f"{indent}    id: '{self._ts_single_quoted('/'.join((*node.path, 'index')))}',",
                    f"{indent}  }},",
                ]
            )
        lines.append(f"{indent}  items: [")
        for child in self._sorted_children(node.children, sort_order_map):
            self._render_docs_node(lines, child, indent_level + 2, sort_order_map, article_order)
        for article in self._sorted_articles(node.articles, article_order):
            lines.append(f"{indent}    '{self._ts_single_quoted(article.doc_id)}',")
        lines.extend([f"{indent}  ],", f"{indent}}},"])

    def _find_node(self, roots: dict[str, DocsSidebarNode], path: tuple[str, ...]) -> DocsSidebarNode | None:
        current = roots.get(path[0]) if path else None
        for segment in path[1:]:
            if current is None:
                return None
            current = current.children.get(segment)
        return current

    def _blog_sidebar_items(
        self,
        categories: tuple[SiteCategorySnapshot, ...],
        articles: tuple[SiteArticleSnapshot, ...],
    ) -> list[BlogSidebarItem]:
        top_categories = [category for category in categories if len(category.path) == 1]
        existing_by_path = {item.path: item for item in self.blog_sidebar.list_registered_categories()}
        articles_by_top: dict[str, list[SiteArticleSnapshot]] = {}
        for article in articles:
            if not article.category_path:
                continue
            articles_by_top.setdefault(article.category_path[0], []).append(article)

        items: list[BlogSidebarItem] = []
        for category in top_categories:
            slug = category.path[0]
            existing = existing_by_path.get(slug)
            doc_items = tuple(
                BlogSidebarDocItem(label=article.title, to=f"/blog/{article.slug}")
                for article in sorted(articles_by_top.get(slug, []), key=lambda item: item.date, reverse=True)
            )
            items.append(
                BlogSidebarItem(
                    label=category.label,
                    path=slug,
                    to=f"/blog/{slug}",
                    count=len(doc_items),
                    collapsed=existing.collapsed if existing else None,
                    items=doc_items,
                )
            )
        return items

    def _docs_nav_items(
        self,
        categories: tuple[SiteCategorySnapshot, ...],
        sort_order_map: dict[tuple[str, tuple[str, ...]], int],
    ) -> list[tuple[str, str]]:
        items = [("/docs/", "首页")]
        top_categories = [category for category in categories if len(category.path) == 1]
        for category in sorted(top_categories, key=lambda item: self._sort_key_for_path(item.path, sort_order_map)):
            items.append((f"/docs/{category.path[0]}", category.label))
        return items

    def _blog_nav_items(self, categories: tuple[SiteCategorySnapshot, ...]) -> list[tuple[str, str]]:
        items = [("/blog", "博客首页")]
        for category in sorted((item for item in categories if len(item.path) == 1), key=lambda item: item.path[0]):
            items.append((f"/blog/{category.path[0]}", category.label))
        return items

    @staticmethod
    def _current_content(path: Path) -> str:
        return path.read_text(encoding="utf-8") if path.exists() else ""

    @staticmethod
    def _ts_single_quoted(value: str) -> str:
        return value.replace("\\", "\\\\").replace("'", "\\'")
