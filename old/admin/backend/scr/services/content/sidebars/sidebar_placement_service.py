"""Insertion and placement helpers for docs sidebars."""

from __future__ import annotations

from dataclasses import dataclass
import re

from scr.core.exceptions import BadRequestError
from scr.services.content.sidebars.sidebar_parser_service import SidebarParserService


@dataclass(frozen=True)
class SidebarInsertion:
    """描述对 sidebars.ts 的一次插入/替换操作。"""

    index: int
    text: str
    replace_until: int | None = None


class SidebarPlacementService:
    """Calculate where sidebar entries/categories should be written."""

    def __init__(self, parser: SidebarParserService | None = None) -> None:
        self.parser = parser or SidebarParserService()

    def find_insertion(self, content: str, doc_id: str) -> SidebarInsertion:
        """定位插入点：在同级（同父分类）最后一个锚点行之后追加。"""
        parent = self.parser.parent_of(doc_id)
        candidate_matches = [
            match
            for match in self.parser.doc_id_pattern.finditer(content)
            if self.parser.is_doc_id_match(content, match) and self.parser.parent_of(match.group(1)) == parent
        ]

        if not candidate_matches:
            raise BadRequestError(
                "目标 docs 分类在 sidebars.ts 中没有同级文章锚点，暂不能自动追加。",
                code="sidebar_anchor_missing",
                details={"doc_id": doc_id, "parent": parent},
            )

        anchor = candidate_matches[-1]
        line_start = content.rfind("\n", 0, anchor.start()) + 1
        line_end = content.find("\n", anchor.end())
        if line_end == -1:
            line_end = len(content)

        line = content[line_start:line_end]
        if "items:" in line and "[" in line and "]" in line:
            return self.expand_inline_items_line(line_start, line_end, line, doc_id)

        indent = line[: len(line) - len(line.lstrip())]
        return SidebarInsertion(
            index=line_end + 1,
            text=f"{indent}'{doc_id}',\n",
        )

    def expand_inline_items_line(
        self,
        line_start: int,
        line_end: int,
        line: str,
        doc_id: str,
    ) -> SidebarInsertion:
        """将单行 `items: [a, b]` 展开为多行写法，并把新 doc_id 追加到末尾。"""
        line_indent = line[: len(line) - len(line.lstrip())]
        item_indent = f"{line_indent}  "
        values = [
            match.group(1)
            for match in self.parser.doc_id_pattern.finditer(line)
            if self.parser.is_doc_id_match(line, match)
        ]

        if not values:
            raise BadRequestError(
                "无法解析 sidebars.ts 中的 inline items 行。",
                code="sidebar_inline_parse_failed",
            )

        rewritten_lines = [
            f"{line_indent}items: [",
            *[f"{item_indent}'{value}'," for value in values],
            f"{item_indent}'{doc_id}',",
            f"{line_indent}],",
        ]

        return SidebarInsertion(
            index=line_start,
            text="\n".join(rewritten_lines) + "\n",
            replace_until=line_end + 1,
        )

    def insert_doc_with_categories(self, content: str, doc_id: str, category_path: list[str], labels: list[str]) -> str:
        """在缺少同级锚点时，按分类层级把 doc_id 写入 sidebars.ts 的正确位置。"""
        if not labels:
            return self.insert_into_first_sidebar(content, f"'{doc_id}',")

        blocks: list[tuple[int, int]] = []
        within: tuple[int, int] | None = None
        for label in labels:
            block = self.parser.find_category_block(content, label, within=within)
            if block is None:
                break
            blocks.append(block)
            within = block

        if not blocks:
            top_slug = category_path[0] if category_path else ""
            return self.append_sidebar_group(content, top_slug, labels[0], labels[1:], doc_id)

        deepest = blocks[-1]
        remaining = labels[len(blocks) :]
        if not remaining:
            return self.insert_into_category_items(content, deepest, f"'{doc_id}',")

        tail = self.category_item_text(remaining[0], remaining[1:], doc_id)
        return self.insert_into_category_items(content, deepest, tail)

    def ensure_category_path_in_content(self, content: str, category_path: list[str], labels: list[str]) -> str:
        top_slug = category_path[0]
        top_label = labels[0]
        group = self.parser.find_sidebar_group(content, top_slug)
        if group is None:
            content = self.append_empty_sidebar_group(content, top_slug, top_label)
            group = self.parser.find_sidebar_group(content, top_slug)
        if group is None:
            raise BadRequestError("sidebars.ts 格式无法识别。", code="sidebars_parse_failed")

        top_block = self.parser.find_category_block(content, top_label, within=group)
        if top_block is None:
            content = self.insert_into_sidebar_group(content, group, self.empty_category_item_text(top_label, top_slug))
            group = self.parser.find_sidebar_group(content, top_slug)
            top_block = self.parser.find_category_block(content, top_label, within=group) if group else None
        if top_block is None:
            raise BadRequestError("sidebars.ts 一级分类写入失败。", code="sidebars_parse_failed")

        current_block = top_block
        for index, label in enumerate(labels[1:], start=1):
            child = self.parser.find_category_block(content, label, within=current_block)
            if child is None:
                content = self.insert_into_category_items(content, current_block, self.empty_category_item_text(label))
                group = self.parser.find_sidebar_group(content, top_slug)
                current_block = (
                    self.parser.find_nested_category_block(content, labels[:index], within=group)
                    if group is not None
                    else None
                )
                if current_block is None:
                    raise BadRequestError("sidebars.ts 分类写入失败。", code="sidebars_parse_failed")
                child = self.parser.find_category_block(content, label, within=current_block)
            if child is None:
                raise BadRequestError("sidebars.ts 分类写入失败。", code="sidebars_parse_failed")
            current_block = child
        return content

    def append_sidebar_group(self, content: str, top_slug: str, top_label: str, remaining_labels: list[str], doc_id: str) -> str:
        sidebar_key = self.parser.sidebar_key(top_slug)
        item_text = self.indent_block(self.category_item_text(top_label, remaining_labels, doc_id), "    ")
        group = f"\n  '{sidebar_key}': [\n{item_text}\n  ],\n"
        insert_at = content.rfind("};")
        if insert_at == -1:
            raise BadRequestError("sidebars.ts 格式无法识别。", code="sidebars_parse_failed")
        return content[:insert_at] + group + content[insert_at:]

    def append_empty_sidebar_group(self, content: str, top_slug: str, top_label: str) -> str:
        sidebar_key = self.parser.sidebar_key(top_slug)
        item_text = self.indent_block(self.empty_category_item_text(top_label, top_slug), "    ")
        group = f"\n  '{sidebar_key}': [\n{item_text}\n  ],\n"
        insert_at = content.rfind("};")
        if insert_at == -1:
            raise BadRequestError("sidebars.ts 格式无法识别。", code="sidebars_parse_failed")
        return content[:insert_at] + group + content[insert_at:]

    def insert_into_sidebar_group(self, content: str, group: tuple[int, int], item_text: str) -> str:
        bracket_index = group[0]
        close_index = group[1] - 1
        closing_line_start = content.rfind("\n", 0, close_index) + 1
        closing_indent = content[closing_line_start:close_index]
        item_indent = f"{closing_indent}  "
        normalized = self.indent_block(item_text, item_indent)
        return self.insert_before_closing_bracket(content, bracket_index if close_index < bracket_index else close_index, normalized)

    def insert_into_first_sidebar(self, content: str, item_text: str) -> str:
        match = re.search(r"\w+\s*:\s*\[", content)
        if not match:
            raise BadRequestError("sidebars.ts 格式无法识别。", code="sidebars_parse_failed")
        bracket_index = content.find("[", match.start())
        close_index = self.parser.find_matching(content, bracket_index, "[", "]")
        return self.insert_before_closing_bracket(content, close_index, f"    {item_text}")

    def insert_into_category_items(self, content: str, block: tuple[int, int], item_text: str) -> str:
        block_text = content[block[0] : block[1]]
        items_match = re.search(r"\bitems\s*:\s*\[", block_text)
        if not items_match:
            raise BadRequestError("sidebars.ts 分类缺少 items。", code="sidebars_parse_failed")
        bracket_index = block[0] + block_text.find("[", items_match.start())
        close_index = self.parser.find_matching(content, bracket_index, "[", "]")
        closing_line_start = content.rfind("\n", 0, close_index) + 1
        closing_indent = content[closing_line_start:close_index]
        item_indent = f"{closing_indent}  "
        normalized = self.indent_block(item_text, item_indent)
        return self.insert_before_closing_bracket(content, close_index, normalized)

    def insert_category_doc_link(self, content: str, block: tuple[int, int], doc_id: str) -> str:
        block_text = content[block[0] : block[1]]
        field_match = (
            re.search(r"^[ \t]*collapsed\s*:[^\n]*(?:\r?\n|$)", block_text, re.MULTILINE)
            or re.search(r"^[ \t]*label\s*:[^\n]*(?:\r?\n|$)", block_text, re.MULTILINE)
            or re.search(r"^[ \t]*type\s*:[^\n]*(?:\r?\n|$)", block_text, re.MULTILINE)
        )
        if not field_match:
            raise BadRequestError("sidebars.ts 分类格式无法识别。", code="sidebars_parse_failed")

        insertion_at = block[0] + field_match.end()
        line = field_match.group(0)
        indent = line[: len(line) - len(line.lstrip())]
        link_text = "\n".join(
            [
                f"{indent}link: {{",
                f"{indent}  type: 'doc',",
                f"{indent}  id: '{self.parser.escape_string(doc_id)}',",
                f"{indent}}},",
                "",
            ]
        )
        return content[:insertion_at] + link_text + content[insertion_at:]

    @staticmethod
    def insert_before_closing_bracket(content: str, close_index: int, item_text: str) -> str:
        line_start = content.rfind("\n", 0, close_index) + 1
        closing_indent = content[line_start:close_index]
        if closing_indent.strip():
            closing_indent = ""
        body = content[:close_index].rstrip()
        suffix = content[close_index:]
        return f"{body}\n{item_text}\n{closing_indent}{suffix}"

    @staticmethod
    def indent_block(text: str, prefix: str) -> str:
        return "\n".join(f"{prefix}{line}" if line else line for line in text.splitlines())

    def category_item_text(self, label: str, remaining_labels: list[str], doc_id: str, *, base_indent: int = 0) -> str:
        indent = " " * base_indent
        inner = " " * (base_indent + 2)
        if remaining_labels:
            child = self.category_item_text(
                remaining_labels[0], remaining_labels[1:], doc_id, base_indent=base_indent + 4
            )
        else:
            child = f"{' ' * (base_indent + 4)}'{doc_id}',"

        return "\n".join(
            [
                f"{indent}{{",
                f"{inner}type: 'category',",
                f"{inner}label: '{self.parser.escape_string(label)}',",
                f"{inner}collapsed: false,",
                f"{inner}items: [",
                child,
                f"{inner}],",
                f"{indent}}},",
            ]
        )

    def empty_category_item_text(self, label: str, top_slug: str | None = None) -> str:
        lines = [
            "{",
            "  type: 'category',",
            f"  label: '{self.parser.escape_string(label)}',",
            "  collapsed: false,",
        ]
        if top_slug:
            lines.extend(
                [
                    "  link: {",
                    "    type: 'doc',",
                    f"    id: '{self.parser.escape_string(top_slug)}/index',",
                    "  },",
                ]
            )
        lines.extend(
            [
                "  items: [",
                "  ],",
                "},",
            ]
        )
        return "\n".join(lines)
