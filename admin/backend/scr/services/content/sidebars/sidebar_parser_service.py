"""Pure parsing and text rewrite helpers for ``site/sidebars.ts``."""

from __future__ import annotations

import re

from scr.core.exceptions import BadRequestError


class SidebarParserService:
    """Parse sidebar text without touching the filesystem."""

    doc_id_pattern = re.compile(r"['\"]([^'\"\n]+)['\"]")

    def registered_doc_ids_from_content(self, content: str) -> list[str]:
        return [
            match.group(1)
            for match in self.doc_id_pattern.finditer(content)
            if self.is_doc_id_match(content, match)
        ]

    def remove_doc_id_from_content(self, content: str, doc_id: str) -> str:
        """删除 sidebars.ts 中的 doc_id 字面量，优先处理独占行，再兼容 inline items。"""
        literal_pattern = re.escape(doc_id)
        line_pattern = re.compile(
            rf"^[ \t]*['\"]{literal_pattern}['\"],[ \t]*(?://[^\n]*)?\r?\n?",
            re.MULTILINE,
        )
        updated, count = line_pattern.subn("", content, count=1)
        if count:
            return updated

        inline_patterns = [
            rf"['\"]{literal_pattern}['\"],[ \t]*",
            rf",[ \t]*['\"]{literal_pattern}['\"]",
            rf"['\"]{literal_pattern}['\"]",
        ]
        for pattern in inline_patterns:
            updated, count = re.subn(pattern, "", content, count=1)
            if count:
                return updated

        return content

    @staticmethod
    def is_doc_id_match(content: str, match: re.Match[str]) -> bool:
        line_start = content.rfind("\n", 0, match.start()) + 1
        line_end = content.find("\n", match.end())
        if line_end == -1:
            line_end = len(content)
        prefix = content[line_start : match.start()]
        suffix = content[match.end() : line_end].strip()
        if suffix.startswith(":"):
            return False
        return not re.search(r"\blabel\s*:\s*$|\btype\s*:\s*$|\btitle\s*:\s*$|\bfrom\s*$", prefix)

    def find_category_block(self, content: str, label: str, within: tuple[int, int] | None = None) -> tuple[int, int] | None:
        escaped_label = re.escape(label)
        start, end = within or (0, len(content))
        pattern = re.compile(rf"\blabel\s*:\s*['\"]{escaped_label}['\"]")
        for match in pattern.finditer(content, start, end):
            block_start = content.rfind("{", start, match.start())
            if block_start == -1:
                continue
            block_end = self.find_matching(content, block_start, "{", "}") + 1
            if block_end <= end:
                return (block_start, block_end)
        return None

    def find_nested_category_block(
        self,
        content: str,
        labels: list[str],
        within: tuple[int, int] | None = None,
    ) -> tuple[int, int] | None:
        block: tuple[int, int] | None = None
        for label in labels:
            block = self.find_category_block(content, label, within=within)
            if block is None:
                return None
            within = block
        return block

    def find_sidebar_group(self, content: str, top_slug: str) -> tuple[int, int] | None:
        sidebar_key = re.escape(self.sidebar_key(top_slug))
        pattern = re.compile(rf"(?:['\"]{sidebar_key}['\"]|{sidebar_key})\s*:\s*\[")
        match = pattern.search(content)
        if not match:
            return None
        bracket_index = content.find("[", match.start())
        if bracket_index == -1:
            return None
        return (bracket_index, self.find_matching(content, bracket_index, "[", "]") + 1)

    def find_sidebar_group_block(self, content: str, top_slug: str) -> tuple[int, int] | None:
        sidebar_key = re.escape(self.sidebar_key(top_slug))
        pattern = re.compile(rf"^[ \t]*(?:['\"]{sidebar_key}['\"]|{sidebar_key})\s*:\s*\[", re.MULTILINE)
        match = pattern.search(content)
        if not match:
            return None
        bracket_index = content.find("[", match.start())
        bracket_end = self.find_matching(content, bracket_index, "[", "]") + 1
        end = bracket_end
        while end < len(content) and content[end] in " \t":
            end += 1
        if end < len(content) and content[end] == ",":
            end += 1
        if end < len(content) and content[end] in "\r\n":
            end += 2 if content[end : end + 2] == "\r\n" else 1
        return match.start(), end

    @staticmethod
    def expand_to_removable_item(content: str, block: tuple[int, int]) -> tuple[int, int]:
        start = content.rfind("\n", 0, block[0]) + 1
        end = block[1]
        while end < len(content) and content[end] in " \t":
            end += 1
        if end < len(content) and content[end] == ",":
            end += 1
        if end < len(content) and content[end] in "\r\n":
            end += 2 if content[end : end + 2] == "\r\n" else 1
        return start, end

    def rename_sidebar_group_key(self, content: str, old_slug: str, new_slug: str) -> str:
        old_key = re.escape(self.sidebar_key(old_slug))
        new_key = self.sidebar_key(new_slug)
        pattern = re.compile(rf"(?P<quote>['\"]?){old_key}(?P=quote)(\s*:\s*\[)")
        return pattern.sub(lambda match: f"{match.group('quote')}{new_key}{match.group('quote')}{match.group(2)}", content, count=1)

    def replace_category_label_in_block(self, content: str, block: tuple[int, int], new_label: str) -> str:
        block_text = content[block[0] : block[1]]
        updated_block = re.sub(
            r"(\blabel\s*:\s*['\"])([^'\"]*)(['\"])",
            lambda match: f"{match.group(1)}{self.escape_string(new_label)}{match.group(3)}",
            block_text,
            count=1,
        )
        return content[: block[0]] + updated_block + content[block[1] :]

    def replace_category_doc_link_id(self, content: str, block: tuple[int, int], new_doc_id: str) -> str:
        block_text = content[block[0] : block[1]]
        link_match = re.search(r"\blink\s*:\s*\{", block_text)
        if not link_match:
            return content
        link_start = block[0] + block_text.find("{", link_match.start())
        link_end = self.find_matching(content, link_start, "{", "}") + 1
        link_text = content[link_start:link_end]
        updated_link = re.sub(
            r"(\bid\s*:\s*['\"])([^'\"]*)(['\"])",
            lambda match: f"{match.group(1)}{self.escape_string(new_doc_id)}{match.group(3)}",
            link_text,
            count=1,
        )
        return content[:link_start] + updated_link + content[link_end:]

    @staticmethod
    def replace_doc_id_prefix(content: str, old_prefix: str, new_prefix: str) -> str:
        old_prefix = old_prefix.strip("/")
        new_prefix = new_prefix.strip("/")
        if not old_prefix or old_prefix == new_prefix:
            return content
        escaped_old_prefix = re.escape(old_prefix)
        literal_pattern = re.compile(rf"(['\"])({escaped_old_prefix})(/[^'\"]*|/index)?(['\"])")

        def replace(match: re.Match[str]) -> str:
            suffix = match.group(3) or ""
            return f"{match.group(1)}{new_prefix}{suffix}{match.group(4)}"

        return literal_pattern.sub(replace, content)

    @staticmethod
    def category_field_indent(block_text: str) -> str:
        match = re.search(r"^([ \t]*)(?:type|label|collapsed)\s*:", block_text, re.MULTILINE)
        if not match:
            return ""
        return match.group(1)

    @staticmethod
    def find_matching(content: str, start_index: int, opener: str, closer: str) -> int:
        depth = 0
        quote: str | None = None
        escaped = False
        for index in range(start_index, len(content)):
            char = content[index]
            if quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
                continue
            if char in {"'", '"', "`"}:
                quote = char
                continue
            if char == opener:
                depth += 1
            elif char == closer:
                depth -= 1
                if depth == 0:
                    return index
        raise BadRequestError("sidebars.ts 括号结构无法解析。", code="sidebars_parse_failed")

    @staticmethod
    def sidebar_key(top_slug: str) -> str:
        return f"{top_slug}Sidebar"

    @staticmethod
    def escape_string(value: str) -> str:
        return value.replace("\\", "\\\\").replace("'", "\\'")

    @staticmethod
    def parent_of(doc_id: str) -> str:
        """取 doc_id 的父级分类：返回目录部分，顶层 doc_id 返回空串。"""
        return doc_id.rsplit("/", 1)[0] if "/" in doc_id else ""
