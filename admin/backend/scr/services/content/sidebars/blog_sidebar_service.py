"""博客侧边栏配置服务。

维护 ``site/blogSidebars.ts``，只登记 ``site/blog`` 下的一级分类目录。
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from scr.core.config import settings
from scr.models.article import ArticleType
from scr.schemas.sidebar import BlogSidebarCategoryDTO
from scr.services.content.categories.category_service import CategoryService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.filesystem.markdown_service import MarkdownService


@dataclass(frozen=True)
class BlogSidebarDocItem:
    """blog 侧边栏中的文章项。"""

    label: str
    to: str


@dataclass(frozen=True)
class BlogSidebarItem:
    """``blogSidebars.ts`` 中一个一级分类项。"""

    label: str
    path: str
    to: str
    count: int | None = None
    collapsed: bool | None = None
    items: tuple[BlogSidebarDocItem, ...] = ()


class BlogSidebarService:
    """读取并生成 blog 专用侧边栏配置。"""

    _object_re = re.compile(r"\{(?P<body>.*?)\}", re.DOTALL)
    _string_field_re = re.compile(
        r"\b(?P<key>label|path|to)\s*:\s*(?P<quote>['\"])(?P<value>(?:(?!(?P=quote)).)*)(?P=quote)"
    )
    _count_re = re.compile(r"\bcount\s*:\s*(\d+)")
    _collapsed_re = re.compile(r"\bcollapsed\s*:\s*(true|false)")

    def __init__(self) -> None:
        self.category = CategoryService()
        self.filesystem = FileSystemService()
        self.markdown = MarkdownService()

    def list_registered_categories(self) -> list[BlogSidebarItem]:
        """返回当前 ``blogSidebars.ts`` 中登记的分类项。"""
        if not settings.blog_sidebars_path.exists():
            return []
        return self._items_from_content(settings.blog_sidebars_path.read_text(encoding="utf-8"))

    def actual_categories(self) -> list[BlogSidebarItem]:
        """从 ``site/blog`` 一级目录与分类注册表推导应存在的分类项。"""
        article_items = self._article_items_by_top_category()
        items: list[BlogSidebarItem] = []
        for category in self.category.list_categories(
            article_type=ArticleType.blog,
            include_empty=True,
            include_counts=True,
        ):
            if len(category.path) != 1:
                continue
            slug = category.path[0]
            if not (settings.blog_dir / slug).is_dir():
                continue
            items.append(
                BlogSidebarItem(
                    label=category.label,
                    path=slug,
                    to=f"/blog/{slug}",
                    count=len(article_items.get(slug, ())),
                    items=article_items.get(slug, ()),
                )
            )
        return sorted(items, key=lambda item: item.path)

    def write_categories(self, items: list[BlogSidebarItem]) -> None:
        """用给定分类项重写 ``blogSidebars.ts``。"""
        settings.blog_sidebars_path.parent.mkdir(parents=True, exist_ok=True)
        settings.blog_sidebars_path.write_text(self._render(items), encoding="utf-8")

    def synced_categories(self) -> list[BlogSidebarItem]:
        """返回实际分类与现有配置合并后的同步结果。

        以真实一级分类为准，清理已不存在的项；保留已有项上的 ``collapsed`` 设置。
        """
        existing_by_path = {item.path: item for item in self.list_registered_categories()}
        synced: list[BlogSidebarItem] = []
        for item in self.actual_categories():
            existing = existing_by_path.get(item.path)
            synced.append(
                BlogSidebarItem(
                    label=item.label,
                    path=item.path,
                    to=item.to,
                    count=item.count,
                    collapsed=existing.collapsed if existing else item.collapsed,
                    items=item.items,
                )
            )
        return synced

    def missing_categories(self) -> list[BlogSidebarItem]:
        actual = {item.path: item for item in self.actual_categories()}
        registered = {item.path for item in self.list_registered_categories()}
        return [actual[path] for path in sorted(actual.keys() - registered)]

    def orphan_categories(self) -> list[BlogSidebarItem]:
        actual = {item.path for item in self.actual_categories()}
        return [item for item in self.list_registered_categories() if item.path not in actual]

    def _article_items_by_top_category(self) -> dict[str, tuple[BlogSidebarDocItem, ...]]:
        grouped: dict[str, list[tuple[str, BlogSidebarDocItem]]] = {}
        for path in self.filesystem.scan_article_files(ArticleType.blog):
            relative = self.filesystem.relative_posix_path(ArticleType.blog, path)
            parts = [part for part in relative.split("/") if part]
            if len(parts) < 2:
                continue
            parsed = self.markdown.parse(path.read_text(encoding="utf-8"))
            frontmatter = parsed.frontmatter
            slug = str(frontmatter.get("slug") or path.stem).strip().lstrip("/")
            date = str(frontmatter.get("date") or "")
            grouped.setdefault(parts[0], []).append(
                (
                    date,
                    BlogSidebarDocItem(
                        label=str(frontmatter.get("title") or path.stem),
                        to=f"/blog/{slug}",
                    ),
                )
            )
        return {
            category: tuple(item for _date, item in sorted(entries, key=lambda current: current[0], reverse=True))
            for category, entries in grouped.items()
        }

    def _items_from_content(self, content: str) -> list[BlogSidebarItem]:
        items: list[BlogSidebarItem] = []
        for match in self._object_re.finditer(content):
            body = match.group("body")
            fields = {
                field_match.group("key"): self._unescape_string(field_match.group("value"))
                for field_match in self._string_field_re.finditer(body)
            }
            if not fields.get("path"):
                continue
            count_match = self._count_re.search(body)
            collapsed_match = self._collapsed_re.search(body)
            items.append(
                BlogSidebarItem(
                    label=fields.get("label") or fields["path"],
                    path=fields["path"],
                    to=fields.get("to") or f"/blog/{fields['path']}",
                    count=int(count_match.group(1)) if count_match else None,
                    collapsed=(collapsed_match.group(1) == "true") if collapsed_match else None,
                )
            )
        return items

    def _render(self, items: list[BlogSidebarItem]) -> str:
        lines = [
            "export type BlogSidebarItem = {",
            "  label: string;",
            "  path: string;",
            "  to: string;",
            "  count?: number;",
            "  collapsed?: boolean;",
            "  items?: BlogSidebarDocItem[];",
            "};",
            "",
            "export type BlogSidebarDocItem = {",
            "  label: string;",
            "  to: string;",
            "};",
            "",
            "const blogSidebars: BlogSidebarItem[] = [",
        ]
        for item in sorted(items, key=lambda current: current.path):
            lines.extend(
                [
                    "  {",
                    f"    label: '{self._ts_single_quoted(item.label)}',",
                    f"    path: '{self._ts_single_quoted(item.path)}',",
                    f"    to: '{self._ts_single_quoted(item.to)}',",
                ]
            )
            if item.collapsed is not None:
                lines.append(f"    collapsed: {str(item.collapsed).lower()},")
            lines.append("    items: [")
            for doc_item in item.items:
                lines.extend(
                    [
                        "      {",
                        f"        label: '{self._ts_single_quoted(doc_item.label)}',",
                        f"        to: '{self._ts_single_quoted(doc_item.to)}',",
                        "      },",
                    ]
                )
            lines.append("    ],")
            lines.extend(["  },"])
        lines.extend(["];", "", "export default blogSidebars;", ""])
        return "\n".join(lines)

    @staticmethod
    def to_dto(item: BlogSidebarItem) -> BlogSidebarCategoryDTO:
        return BlogSidebarCategoryDTO(
            label=item.label,
            path=item.path,
            to=item.to,
            count=item.count,
            collapsed=item.collapsed,
            items=[{"label": doc_item.label, "to": doc_item.to} for doc_item in item.items],
        )

    @staticmethod
    def _ts_single_quoted(value: str) -> str:
        return value.replace("\\", "\\\\").replace("'", "\\'")

    @staticmethod
    def _unescape_string(value: str) -> str:
        return value.replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")
