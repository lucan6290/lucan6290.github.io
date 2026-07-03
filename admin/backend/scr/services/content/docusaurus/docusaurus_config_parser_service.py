"""Pure text helpers for ``site/docusaurus.config.ts``.

The config file is TypeScript, but the admin backend only needs a small,
well-defined subset of navbar parsing.  This service keeps the bracket
matching and string escaping logic isolated from file IO and workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class NavItemInfo:
    """A ``navbar.items`` object that contains a ``to`` field."""

    to: str
    label: str | None
    dropdown_label: str | None
    object_start: int
    object_end: int


class DocusaurusConfigParserService:
    """Parse and edit navbar blocks in Docusaurus config text."""

    _field_value_re = re.compile(
        r"(?<![A-Za-z0-9_])(?P<key>label|type|to)\s*:\s*"
        r"(?P<quote>['\"`])(?P<val>(?:(?!(?P=quote)).)*)(?P=quote)"
    )
    _navbar_block_re = re.compile(r"\bnavbar\s*:\s*\{")

    def scan_navbar_to_items(self, content: str) -> list[NavItemInfo]:
        """Scan ``navbar`` and return all objects that define ``to``."""
        navbar_bounds = self.find_navbar_bounds(content)
        if navbar_bounds is None:
            return []
        _, nav_end = navbar_bounds

        items: list[NavItemInfo] = []
        stack: list[dict] = []
        index = 0 if navbar_bounds[0] < 0 else navbar_bounds[0]
        quote: str | None = None
        escaped = False

        while index < nav_end:
            char = content[index]
            if quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
                index += 1
                continue
            if char in {"'", '"', "`"}:
                quote = char
                index += 1
                continue
            if char == "{":
                stack.append({"open": index, "label": None, "type": None, "to": None})
                index += 1
                continue
            if char == "}":
                if stack:
                    obj = stack.pop()
                    if obj.get("to") is not None:
                        items.append(
                            NavItemInfo(
                                to=obj["to"],
                                label=obj.get("label"),
                                dropdown_label=self.enclosing_dropdown_label(stack),
                                object_start=obj["open"],
                                object_end=index + 1,
                            )
                        )
                index += 1
                continue
            if char.isalpha() or char == "_":
                field_match = self._field_value_re.match(content, index, nav_end)
                if field_match:
                    if stack:
                        stack[-1][field_match.group("key")] = field_match.group("val")
                    index = field_match.end()
                    continue
                ident_match = re.match(r"[A-Za-z_]\w*", content[index:nav_end])
                index += ident_match.end() if ident_match else 1
                continue
            index += 1

        return items

    @staticmethod
    def enclosing_dropdown_label(stack: list[dict]) -> str | None:
        """Return the nearest dropdown ancestor label from a parser stack."""
        for parent in reversed(stack):
            if parent.get("type") == "dropdown" and parent.get("label"):
                return parent["label"]
        return None

    def find_navbar_bounds(self, content: str) -> tuple[int, int] | None:
        """Locate the full ``navbar: { ... }`` object bounds."""
        match = self._navbar_block_re.search(content)
        if not match:
            return None
        brace_start = match.end() - 1
        brace_end = self.find_matching_pair(content, brace_start, "{", "}")
        if brace_end is None:
            return None
        return brace_start, brace_end + 1

    def find_dropdown_nav_item_block(
        self,
        content: str,
        dropdown_label: str,
        route_value: str,
    ) -> tuple[int, int] | None:
        """Find a removable item block in a dropdown by exact ``to`` value."""
        bounds = self.dropdown_items_bounds(content, dropdown_label)
        if bounds is None:
            return None
        items_start, items_end = bounds
        route = re.escape(route_value)
        pattern = re.compile(rf"\bto\s*:\s*(['\"]){route}\1")
        match = pattern.search(content, items_start, items_end)
        if not match:
            return None

        object_start = content.rfind("{", items_start, match.start())
        if object_start == -1:
            return None
        object_end = self.find_matching_pair(content, object_start, "{", "}")
        if object_end is None:
            return None

        return self.expand_to_removable_range(content, object_start, object_end + 1, lower_bound=items_start)

    def dropdown_items_bounds(self, content: str, dropdown_label: str) -> tuple[int, int] | None:
        """Return the ``items: [ ... ]`` array bounds for a dropdown label."""
        label = re.escape(dropdown_label)
        label_match = re.search(rf"\blabel\s*:\s*(['\"]){label}\1", content)
        if not label_match:
            return None
        items_match = re.search(r"\bitems\s*:\s*\[", content[label_match.end():])
        if not items_match:
            return None
        items_start = label_match.end() + items_match.end() - 1
        items_end = self.find_matching_pair(content, items_start, "[", "]")
        if items_end is None:
            return None
        return items_start, items_end

    @staticmethod
    def expand_to_removable_range(
        content: str,
        obj_start: int,
        obj_end: int,
        *,
        lower_bound: int = 0,
    ) -> tuple[int, int]:
        """Expand an object range to include indentation, trailing comma and newline."""
        start = content.rfind("\n", lower_bound, obj_start) + 1
        end = obj_end
        while end < len(content) and content[end] in " \t":
            end += 1
        if end < len(content) and content[end] == ",":
            end += 1
        if end < len(content) and content[end] in "\r\n":
            end += 2 if content[end:end + 2] == "\r\n" else 1
        return start, end

    @staticmethod
    def line_indent(content: str, index: int) -> str:
        line_start = content.rfind("\n", 0, index) + 1
        line = content[line_start:index]
        return line[:len(line) - len(line.lstrip(" \t"))]

    @staticmethod
    def ts_single_quoted(value: str) -> str:
        return value.replace("\\", "\\\\").replace("'", "\\'")

    @staticmethod
    def find_matching_pair(content: str, start: int, open_char: str, close_char: str) -> int | None:
        depth = 0
        quote: str | None = None
        escaped = False
        for index in range(start, len(content)):
            char = content[index]
            if quote:
                if escaped:
                    escaped = False
                    continue
                if char == "\\":
                    escaped = True
                    continue
                if char == quote:
                    quote = None
                continue
            if char in {"'", '"', "`"}:
                quote = char
                continue
            if char == open_char:
                depth += 1
                continue
            if char == close_char:
                depth -= 1
                if depth == 0:
                    return index
        return None
