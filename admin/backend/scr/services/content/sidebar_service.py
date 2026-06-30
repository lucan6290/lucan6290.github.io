"""侧边栏服务。

解析 site/sidebars.ts，提取其中已登记的 doc_id 集合，用于判断 docs 文章是否
已纳入站点导航；同时提供 append_doc_id，将新建 docs 文章的 doc_id 追加写入
侧边栏对应分类下。
"""

from dataclasses import dataclass
import hashlib
import re

from scr.core.config import settings
from scr.core.exceptions import BadRequestError


@dataclass(frozen=True)
class _SidebarInsertion:
    """描述对 sidebars.ts 的一次插入/替换操作。"""

    index: int  # 插入起始位置（字符偏移）
    text: str  # 待写入的文本
    replace_until: int | None = None  # 若需替换原有片段，指定其结束偏移；None 表示纯插入


class SidebarService:
    """读取并维护 Docusaurus 侧边栏配置。"""

    # 匹配 sidebars.ts 中被引号包裹的 doc_id 字面量（兼容单/双引号）
    doc_id_pattern = re.compile(r"['\"]([^'\"\n]+)['\"]")

    def list_registered_doc_ids(self) -> set[str]:
        """返回 sidebars.ts 中出现过的全部 doc_id；配置文件不存在时返回空集。"""
        if not settings.sidebars_path.exists():
            return set()

        content = settings.sidebars_path.read_text(encoding="utf-8")
        return set(self._registered_doc_ids_from_content(content))

    @staticmethod
    def doc_id_from_relative_path(relative_path: str) -> str:
        """由相对路径推导 doc_id：去除扩展名并统一为 posix 风格。"""
        return relative_path.rsplit(".", 1)[0].replace("\\", "/")

    def append_doc_id(self, doc_id: str) -> None:
        """将 doc_id 追加到 sidebars.ts 的同级分类末尾；已存在则跳过。"""
        if not settings.sidebars_path.exists():
            raise BadRequestError("site/sidebars.ts 不存在，无法同步 docs 侧边栏。", code="sidebars_missing")

        content = settings.sidebars_path.read_text(encoding="utf-8")
        if doc_id in self._registered_doc_ids_from_content(content):
            return  # 幂等：已登记则无需重复写入

        insertion = self._find_insertion(content, doc_id)
        # replace_until 为 None 时退化为在 index 处纯插入
        replace_until = insertion.replace_until or insertion.index
        updated = content[: insertion.index] + insertion.text + content[replace_until:]
        settings.sidebars_path.write_text(updated, encoding="utf-8")

    def remove_doc_id(self, doc_id: str) -> bool:
        """从 sidebars.ts 中移除 doc_id；存在并写入变更时返回 True。"""
        if not settings.sidebars_path.exists():
            raise BadRequestError("site/sidebars.ts 不存在，无法同步 docs 侧边栏。", code="sidebars_missing")

        content = settings.sidebars_path.read_text(encoding="utf-8")
        if doc_id not in self._registered_doc_ids_from_content(content):
            return False

        updated = self._remove_doc_id_from_content(content, doc_id)
        settings.sidebars_path.write_text(updated, encoding="utf-8")
        return updated != content

    def replace_doc_id(self, old_doc_id: str, new_doc_id: str) -> bool:
        """在 sidebars.ts 中将旧 doc_id 替换为新 doc_id；存在并写入变更时返回 True。"""
        if not settings.sidebars_path.exists():
            raise BadRequestError("site/sidebars.ts 不存在，无法同步 docs 侧边栏。", code="sidebars_missing")

        content = settings.sidebars_path.read_text(encoding="utf-8")
        if old_doc_id not in self._registered_doc_ids_from_content(content):
            return False

        literal_pattern = re.escape(old_doc_id)
        updated = re.sub(
            rf"(['\"]){literal_pattern}(['\"])",
            lambda match: f"{match.group(1)}{new_doc_id}{match.group(2)}",
            content,
        )
        settings.sidebars_path.write_text(updated, encoding="utf-8")
        return updated != content

    def ensure_doc_id(self, doc_id: str, category_path: list[str], category_labels: list[str]) -> None:
        """确保 doc_id 登记到 sidebars.ts；缺少分类锚点时创建分类结构。"""
        if not settings.sidebars_path.exists():
            raise BadRequestError("site/sidebars.ts 不存在，无法同步 docs 侧边栏。", code="sidebars_missing")

        content = settings.sidebars_path.read_text(encoding="utf-8")
        if doc_id in self._registered_doc_ids_from_content(content):
            return

        try:
            self.append_doc_id(doc_id)
            return
        except BadRequestError as exc:
            if exc.code != "sidebar_anchor_missing":
                raise

        content = settings.sidebars_path.read_text(encoding="utf-8")
        labels = [
            (category_labels[index] if index < len(category_labels) and category_labels[index] else segment)
            for index, segment in enumerate(category_path)
        ]
        updated = self._insert_doc_with_categories(content, doc_id, labels)
        settings.sidebars_path.write_text(updated, encoding="utf-8")

    def _remove_doc_id_from_content(self, content: str, doc_id: str) -> str:
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

    def _find_insertion(self, content: str, doc_id: str) -> _SidebarInsertion:
        """定位插入点：在同级（同父分类）最后一个锚点行之后追加。

        若锚点行是 inline items 形式（`items: [a, b]`），则需先展开为多行再追加。
        """
        parent = self._parent_of(doc_id)
        # 收集与目标 doc_id 属于同一父分类的全部已有锚点
        candidate_matches = [
            match
            for match in self.doc_id_pattern.finditer(content)
            if self._is_doc_id_match(content, match) and self._parent_of(match.group(1)) == parent
        ]

        if not candidate_matches:
            raise BadRequestError(
                "目标 docs 分类在 sidebars.ts 中没有同级文章锚点，暂不能自动追加。",
                code="sidebar_anchor_missing",
                details={"doc_id": doc_id, "parent": parent},
            )

        anchor = candidate_matches[-1]  # 取同级最后一个锚点，保证追加在末尾
        # 定位锚点所在整行
        line_start = content.rfind("\n", 0, anchor.start()) + 1
        line_end = content.find("\n", anchor.end())
        if line_end == -1:
            line_end = len(content)

        line = content[line_start:line_end]
        # 命中 `items: [...]` 单行写法时，需要展开为多行才能整洁地追加新项
        if "items:" in line and "[" in line and "]" in line:
            return self._expand_inline_items_line(line_start, line_end, line, doc_id)

        # 普通多行写法：沿用当前行缩进，在下一行追加新 doc_id
        indent = line[: len(line) - len(line.lstrip())]
        return _SidebarInsertion(
            index=line_end + 1,
            text=f"{indent}'{doc_id}',\n",
        )

    def _expand_inline_items_line(
        self,
        line_start: int,
        line_end: int,
        line: str,
        doc_id: str,
    ) -> _SidebarInsertion:
        """将单行 `items: [a, b]` 展开为多行写法，并把新 doc_id 追加到末尾。"""
        line_indent = line[: len(line) - len(line.lstrip())]
        item_indent = f"{line_indent}  "  # 子项比所属行多缩进两级
        values = [
            match.group(1)
            for match in self.doc_id_pattern.finditer(line)
            if self._is_doc_id_match(line, match)
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

        # 用展开后的多行替换原 inline 行（replace_until 含尾部换行）
        return _SidebarInsertion(
            index=line_start,
            text="\n".join(rewritten_lines) + "\n",
            replace_until=line_end + 1,
        )

    def _registered_doc_ids_from_content(self, content: str) -> list[str]:
        return [
            match.group(1)
            for match in self.doc_id_pattern.finditer(content)
            if self._is_doc_id_match(content, match)
        ]

    @staticmethod
    def _is_doc_id_match(content: str, match: re.Match[str]) -> bool:
        line_start = content.rfind("\n", 0, match.start()) + 1
        prefix = content[line_start : match.start()]
        return not re.search(r"\blabel\s*:\s*$|\btype\s*:\s*$|\btitle\s*:\s*$", prefix)

    def _insert_doc_with_categories(self, content: str, doc_id: str, labels: list[str]) -> str:
        """在缺少同级锚点时，按分类层级把 doc_id 写入 sidebars.ts 的正确位置。

        自顶向下逐层匹配已存在的分类块，定位到最深的已存在祖先：
        - 全部层级都已存在 → 直接把 doc_id 追加进该分类 items；
        - 否则 → 用 _category_item_text 构造缺失的尾部层级，嵌套进最深祖先的 items；
        - 连顶层分类都不存在 → 追加一个全新的侧边栏分组。
        """
        if not labels:
            return self._insert_into_first_sidebar(content, f"'{doc_id}',")

        blocks: list[tuple[int, int]] = []
        within: tuple[int, int] | None = None
        for label in labels:
            block = self._find_category_block(content, label, within=within)
            if block is None:
                break
            blocks.append(block)
            within = block

        if not blocks:
            return self._append_sidebar_group(content, labels[0], labels[1:], doc_id)

        deepest = blocks[-1]
        remaining = labels[len(blocks) :]
        if not remaining:
            # 全部分类层级都已存在：直接把 doc_id 放进最深分类的 items
            return self._insert_into_category_items(content, deepest, f"'{doc_id}',")

        # 最深祖先之后还差若干层级：构造尾部子树，嵌套进最深祖先的 items
        tail = self._category_item_text(remaining[0], remaining[1:], doc_id)
        return self._insert_into_category_items(content, deepest, tail)

    def _append_sidebar_group(self, content: str, top_label: str, remaining_labels: list[str], doc_id: str) -> str:
        sidebar_key = self._sidebar_key(top_label)
        item_text = self._indent_block(self._category_item_text(top_label, remaining_labels, doc_id), "    ")
        group = f"\n  {sidebar_key}: [\n{item_text}\n  ],\n"
        insert_at = content.rfind("};")
        if insert_at == -1:
            raise BadRequestError("sidebars.ts 格式无法识别。", code="sidebars_parse_failed")
        return content[:insert_at] + group + content[insert_at:]

    def _insert_into_first_sidebar(self, content: str, item_text: str) -> str:
        match = re.search(r"\w+\s*:\s*\[", content)
        if not match:
            raise BadRequestError("sidebars.ts 格式无法识别。", code="sidebars_parse_failed")
        bracket_index = content.find("[", match.start())
        close_index = self._find_matching(content, bracket_index, "[", "]")
        return self._insert_before_closing_bracket(content, close_index, f"    {item_text}")

    def _insert_into_category_items(self, content: str, block: tuple[int, int], item_text: str) -> str:
        block_text = content[block[0] : block[1]]
        items_match = re.search(r"\bitems\s*:\s*\[", block_text)
        if not items_match:
            raise BadRequestError("sidebars.ts 分类缺少 items。", code="sidebars_parse_failed")
        bracket_index = block[0] + block_text.find("[", items_match.start())
        close_index = self._find_matching(content, bracket_index, "[", "]")
        closing_line_start = content.rfind("\n", 0, close_index) + 1
        closing_indent = content[closing_line_start:close_index]
        item_indent = f"{closing_indent}  "
        # item_text 来自 _category_item_text，使用相对缩进（0 起）；此处统一加上目标缩进，避免双重缩进
        normalized = self._indent_block(item_text, item_indent)
        return self._insert_before_closing_bracket(content, close_index, normalized)

    @staticmethod
    def _insert_before_closing_bracket(content: str, close_index: int, item_text: str) -> str:
        # 保留闭合 ] 所在行的缩进，避免 rstrip 连同换行把缩进吞掉、导致 ] 落到行首
        line_start = content.rfind("\n", 0, close_index) + 1
        closing_indent = content[line_start:close_index]
        if closing_indent.strip():  # ] 与内容同行（inline items）时无法保留缩进
            closing_indent = ""
        body = content[:close_index].rstrip()
        suffix = content[close_index:]
        return f"{body}\n{item_text}\n{closing_indent}{suffix}"

    @staticmethod
    def _indent_block(text: str, prefix: str) -> str:
        """给多行文本的每个非空行统一加上前导缩进。"""
        return "\n".join(f"{prefix}{line}" if line else line for line in text.splitlines())

    def _category_item_text(self, label: str, remaining_labels: list[str], doc_id: str, *, base_indent: int = 0) -> str:
        """构造一个分类对象的多行文本，缩进为相对值（base_indent 起，每层 +2 空格）。

        实际落位时由 _insert_into_category_items / _append_sidebar_group 统一加上目标缩进，
        避免“已带绝对缩进再被前置 item_indent”造成的双重缩进。
        """
        indent = " " * base_indent
        inner = " " * (base_indent + 2)
        if remaining_labels:
            child = self._category_item_text(
                remaining_labels[0], remaining_labels[1:], doc_id, base_indent=base_indent + 4
            )
        else:
            child = f"{' ' * (base_indent + 4)}'{doc_id}',"

        return "\n".join(
            [
                f"{indent}{{",
                f"{inner}type: 'category',",
                f"{inner}label: '{self._escape_string(label)}',",
                f"{inner}collapsed: false,",
                f"{inner}items: [",
                child,
                f"{inner}],",
                f"{indent}}},",
            ]
        )

    def _find_category_block(self, content: str, label: str, within: tuple[int, int] | None = None) -> tuple[int, int] | None:
        escaped_label = re.escape(label)
        start, end = within or (0, len(content))
        pattern = re.compile(rf"\blabel\s*:\s*['\"]{escaped_label}['\"]")
        for match in pattern.finditer(content, start, end):
            block_start = content.rfind("{", start, match.start())
            if block_start == -1:
                continue
            block_end = self._find_matching(content, block_start, "{", "}") + 1
            if block_end <= end:
                return (block_start, block_end)
        return None

    @staticmethod
    def _find_matching(content: str, start_index: int, opener: str, closer: str) -> int:
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
    def _sidebar_key(label: str) -> str:
        digest = hashlib.sha1(label.encode("utf-8")).hexdigest()[:10]
        return f"generated{digest}Sidebar"

    @staticmethod
    def _escape_string(value: str) -> str:
        return value.replace("\\", "\\\\").replace("'", "\\'")

    @staticmethod
    def _parent_of(doc_id: str) -> str:
        """取 doc_id 的父级分类：返回目录部分，顶层 doc_id 返回空串。"""
        return doc_id.rsplit("/", 1)[0] if "/" in doc_id else ""
