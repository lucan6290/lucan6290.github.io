"""Top navbar maintenance for Docusaurus config text."""

from __future__ import annotations

import re

from scr.core.exceptions import BadRequestError
from scr.services.content.docusaurus.docusaurus_config_parser_service import (
    DocusaurusConfigParserService,
)


class DocusaurusNavService:
    """Maintain docs/blog dropdown items in ``themeConfig.navbar`` text."""

    def __init__(self) -> None:
        self.parser = DocusaurusConfigParserService()

    def knowledge_nav_item_exists(self, content: str, slug: str) -> bool:
        return self.parser.find_dropdown_nav_item_block(content, "知识库", self.knowledge_route(slug)) is not None

    def upsert_knowledge_nav_item(self, content: str, slug: str, label: str) -> str:
        updated = self.replace_knowledge_nav_item(content, slug, slug, label)
        if updated is not None:
            return updated
        return self.insert_knowledge_nav_item(content, slug, label)

    def update_knowledge_nav_item_label(self, content: str, slug: str, label: str) -> str | None:
        return self.replace_knowledge_nav_item(content, slug, slug, label)

    def replace_knowledge_nav_item(
        self,
        content: str,
        old_slug: str,
        new_slug: str,
        label: str,
    ) -> str | None:
        block = self.parser.find_dropdown_nav_item_block(content, "知识库", self.knowledge_route(old_slug))
        if block is None:
            return None
        indent = self.parser.line_indent(content, block[0])
        item = self.nav_item_text(indent, self.knowledge_route(new_slug), label)
        return content[:block[0]] + item + content[block[1]:]

    def remove_knowledge_nav_item(self, content: str, slug: str) -> str | None:
        block = self.parser.find_dropdown_nav_item_block(content, "知识库", self.knowledge_route(slug))
        if block is None:
            return None
        return content[:block[0]] + content[block[1]:]

    def blog_nav_item_exists(self, content: str, slug: str) -> bool:
        return self.parser.find_dropdown_nav_item_block(content, "博客", self.blog_route(slug)) is not None

    def upsert_blog_nav_item(self, content: str, slug: str, label: str) -> str:
        route = self.blog_route(slug)
        updated = self.replace_dropdown_nav_item(content, "博客", route, label)
        if updated is not None:
            return updated
        return self.insert_dropdown_nav_item(content, "博客", route, label)

    def replace_blog_nav_item(
        self,
        content: str,
        old_slug: str,
        new_slug: str,
        label: str,
    ) -> str | None:
        block = self.parser.find_dropdown_nav_item_block(content, "博客", self.blog_route(old_slug))
        if block is None:
            return None
        indent = self.parser.line_indent(content, block[0])
        item = self.nav_item_text(indent, self.blog_route(new_slug), label)
        return content[:block[0]] + item + content[block[1]:]

    def remove_blog_nav_item(self, content: str, slug: str) -> str | None:
        block = self.parser.find_dropdown_nav_item_block(content, "博客", self.blog_route(slug))
        if block is None:
            return None
        return content[:block[0]] + content[block[1]:]

    def replace_dropdown_nav_item(
        self,
        content: str,
        dropdown_label: str,
        route: str,
        label: str,
    ) -> str | None:
        block = self.parser.find_dropdown_nav_item_block(content, dropdown_label, route)
        if block is None:
            return None
        indent = self.parser.line_indent(content, block[0])
        item = self.nav_item_text(indent, route, label)
        return content[:block[0]] + item + content[block[1]:]

    def insert_knowledge_nav_item(self, content: str, slug: str, label: str) -> str:
        bounds = self.parser.dropdown_items_bounds(content, "知识库")
        if bounds is None:
            raise BadRequestError(
                "未找到 label: '知识库' 的顶部导航配置。",
                code="knowledge_nav_missing",
            )
        return self.insert_nav_item_at_bounds(content, bounds, self.knowledge_route(slug), label)

    def insert_dropdown_nav_item(self, content: str, dropdown_label: str, route: str, label: str) -> str:
        bounds = self.parser.dropdown_items_bounds(content, dropdown_label)
        if bounds is None:
            raise BadRequestError(
                f"未找到 label: '{dropdown_label}' 的顶部导航配置。",
                code="dropdown_nav_missing",
                details={"dropdown_label": dropdown_label},
            )
        return self.insert_nav_item_at_bounds(content, bounds, route, label)

    def insert_nav_item_at_bounds(
        self,
        content: str,
        bounds: tuple[int, int],
        route: str,
        label: str,
    ) -> str:
        items_start, items_end = bounds
        body = content[items_start + 1:items_end]
        match = re.search(r"\n([ \t]*)\{", body)
        item_indent = match.group(1) if match else f"{self.parser.line_indent(content, items_start)}  "
        item = self.nav_item_text(item_indent, route, label)
        prefix = "" if content[:items_end].endswith("\n") else "\n"
        return content[:items_end] + prefix + item + content[items_end:]

    def remove_nav_item_by_to(self, content: str, to: str) -> str | None:
        target = next((item for item in self.parser.scan_navbar_to_items(content) if item.to == to), None)
        if target is None:
            return None
        start, end = self.parser.expand_to_removable_range(content, target.object_start, target.object_end)
        return content[:start] + content[end:]

    @classmethod
    def nav_item_text(cls, indent: str, route: str, label: str) -> str:
        parser = DocusaurusConfigParserService
        return (
            f"{indent}{{\n"
            f"{indent}  label: '{parser.ts_single_quoted(label)}',\n"
            f"{indent}  to: '{parser.ts_single_quoted(route)}',\n"
            f"{indent}}},\n"
        )

    @staticmethod
    def knowledge_route(slug: str) -> str:
        return f"/docs/{slug}"

    @staticmethod
    def blog_route(slug: str) -> str:
        return f"/blog/{slug}"
