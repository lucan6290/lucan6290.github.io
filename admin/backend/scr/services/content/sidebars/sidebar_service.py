"""侧边栏服务。

解析 site/sidebars.ts，提取其中已登记的 doc_id 集合，用于判断 docs 文章是否
已纳入站点导航；同时提供 append_doc_id，将新建 docs 文章的 doc_id 追加写入
侧边栏对应分类下。
"""

import re

from scr.core.config import settings
from scr.core.exceptions import BadRequestError
from scr.services.content.sidebars.sidebar_parser_service import SidebarParserService
from scr.services.content.sidebars.sidebar_placement_service import SidebarPlacementService


class SidebarService:
    """读取并维护 Docusaurus 侧边栏配置。"""

    # 匹配 sidebars.ts 中被引号包裹的 doc_id 字面量（兼容单/双引号）
    doc_id_pattern = SidebarParserService.doc_id_pattern

    def __init__(self) -> None:
        self.parser = SidebarParserService()
        self.placement = SidebarPlacementService(self.parser)

    def list_registered_doc_ids(self) -> set[str]:
        """返回 sidebars.ts 中出现过的全部 doc_id；配置文件不存在时返回空集。"""
        if not settings.sidebars_path.exists():
            return set()

        content = settings.sidebars_path.read_text(encoding="utf-8")
        return set(self.parser.registered_doc_ids_from_content(content))

    @staticmethod
    def doc_id_from_relative_path(relative_path: str) -> str:
        """由相对路径推导 doc_id：去除扩展名并统一为 posix 风格。"""
        return relative_path.rsplit(".", 1)[0].replace("\\", "/")

    def append_doc_id(self, doc_id: str) -> None:
        """将 doc_id 追加到 sidebars.ts 的同级分类末尾；已存在则跳过。"""
        if not settings.sidebars_path.exists():
            raise BadRequestError("site/sidebars.ts 不存在，无法同步 docs 侧边栏。", code="sidebars_missing")

        content = settings.sidebars_path.read_text(encoding="utf-8")
        if doc_id in self.parser.registered_doc_ids_from_content(content):
            return  # 幂等：已登记则无需重复写入

        insertion = self.placement.find_insertion(content, doc_id)
        # replace_until 为 None 时退化为在 index 处纯插入
        replace_until = insertion.replace_until or insertion.index
        updated = content[: insertion.index] + insertion.text + content[replace_until:]
        settings.sidebars_path.write_text(updated, encoding="utf-8")

    def remove_doc_id(self, doc_id: str) -> bool:
        """从 sidebars.ts 中移除 doc_id；存在并写入变更时返回 True。"""
        if not settings.sidebars_path.exists():
            raise BadRequestError("site/sidebars.ts 不存在，无法同步 docs 侧边栏。", code="sidebars_missing")

        content = settings.sidebars_path.read_text(encoding="utf-8")
        if doc_id not in self.parser.registered_doc_ids_from_content(content):
            return False

        updated = self.parser.remove_doc_id_from_content(content, doc_id)
        settings.sidebars_path.write_text(updated, encoding="utf-8")
        return updated != content

    def replace_doc_id(self, old_doc_id: str, new_doc_id: str) -> bool:
        """在 sidebars.ts 中将旧 doc_id 替换为新 doc_id；存在并写入变更时返回 True。"""
        if not settings.sidebars_path.exists():
            raise BadRequestError("site/sidebars.ts 不存在，无法同步 docs 侧边栏。", code="sidebars_missing")

        content = settings.sidebars_path.read_text(encoding="utf-8")
        if old_doc_id not in self.parser.registered_doc_ids_from_content(content):
            return False

        literal_pattern = re.escape(old_doc_id)
        updated = re.sub(
            rf"(['\"]){literal_pattern}(['\"])",
            lambda match: f"{match.group(1)}{new_doc_id}{match.group(2)}",
            content,
        )
        settings.sidebars_path.write_text(updated, encoding="utf-8")
        return updated != content

    def move_doc_id_to_existing_category(
        self,
        old_doc_id: str,
        new_doc_id: str,
        target_category_labels: list[str],
    ) -> bool:
        """从旧位置移除 doc_id，并写入已有目标分类块。"""
        if not settings.sidebars_path.exists():
            raise BadRequestError("site/sidebars.ts 不存在，无法同步 docs 侧边栏。", code="sidebars_missing")

        content = settings.sidebars_path.read_text(encoding="utf-8")
        updated = content
        if old_doc_id in self.parser.registered_doc_ids_from_content(updated):
            updated = self.parser.remove_doc_id_from_content(updated, old_doc_id)
        if new_doc_id in self.parser.registered_doc_ids_from_content(updated):
            if updated != content:
                settings.sidebars_path.write_text(updated, encoding="utf-8")
            return updated != content

        if not target_category_labels:
            updated = self.placement.insert_into_first_sidebar(updated, f"'{new_doc_id}',")
        else:
            block = self.parser.find_nested_category_block(updated, target_category_labels)
            if block is None:
                raise BadRequestError(
                    "目标 docs 分类在 sidebars.ts 中不存在，无法移动文章。",
                    code="sidebar_category_missing",
                    details={"doc_id": new_doc_id, "category_labels": target_category_labels},
                )
            updated = self.placement.insert_into_category_items(updated, block, f"'{new_doc_id}',")

        if updated != content:
            settings.sidebars_path.write_text(updated, encoding="utf-8")
            return True
        return False

    def remove_category_path(self, category_path: list[str], category_labels: list[str]) -> bool:
        """删除 sidebars.ts 中的一级 sidebar group 或下级分类块。"""
        if not settings.sidebars_path.exists():
            raise BadRequestError("site/sidebars.ts 不存在，无法同步 docs 侧边栏。", code="sidebars_missing")

        normalized_path = [segment.strip() for segment in category_path if segment.strip()]
        labels = [label.strip() for label in category_labels if label.strip()]
        if not normalized_path or not labels:
            return False

        content = settings.sidebars_path.read_text(encoding="utf-8")
        if len(normalized_path) == 1:
            block = self.parser.find_sidebar_group_block(content, normalized_path[0])
        else:
            block = self.parser.find_nested_category_block(content, labels)
            if block is not None:
                block = self.parser.expand_to_removable_item(content, block)
        if block is None:
            return False

        updated = content[: block[0]] + content[block[1] :]
        if updated != content:
            settings.sidebars_path.write_text(updated, encoding="utf-8")
            return True
        return False

    def rename_category_path(
        self,
        old_path: list[str],
        new_path: list[str],
        old_labels: list[str],
        new_labels: list[str],
    ) -> bool:
        """同步重命名 sidebars.ts 中的分类结构和分类下 doc_id 前缀。"""
        if not settings.sidebars_path.exists():
            raise BadRequestError("site/sidebars.ts 不存在，无法同步 docs 侧边栏。", code="sidebars_missing")

        old_path = [segment.strip() for segment in old_path if segment.strip()]
        new_path = [segment.strip() for segment in new_path if segment.strip()]
        old_labels = [label.strip() for label in old_labels if label.strip()]
        new_labels = [label.strip() for label in new_labels if label.strip()]
        if not old_path or not new_path or not old_labels or not new_labels:
            return False

        content = settings.sidebars_path.read_text(encoding="utf-8")
        updated = content

        if len(old_path) == 1:
            updated = self.parser.rename_sidebar_group_key(updated, old_path[0], new_path[0])
            group = self.parser.find_sidebar_group(updated, new_path[0])
            top_block = self.parser.find_category_block(updated, old_labels[0], within=group) if group else None
            if top_block is not None:
                updated = self.parser.replace_category_label_in_block(updated, top_block, new_labels[0])
                top_block = self.parser.find_category_block(updated, new_labels[0], within=self.parser.find_sidebar_group(updated, new_path[0]))
                if top_block is not None:
                    updated = self.parser.replace_category_doc_link_id(updated, top_block, f"{new_path[0]}/index")
        else:
            block = self.parser.find_nested_category_block(updated, old_labels)
            if block is not None:
                updated = self.parser.replace_category_label_in_block(updated, block, new_labels[-1])

        updated = self.parser.replace_doc_id_prefix(updated, "/".join(old_path), "/".join(new_path))
        if updated != content:
            settings.sidebars_path.write_text(updated, encoding="utf-8")
            return True
        return False

    def ensure_doc_id(self, doc_id: str, category_path: list[str], category_labels: list[str]) -> None:
        """确保 doc_id 登记到 sidebars.ts；缺少分类锚点时创建分类结构。"""
        if not settings.sidebars_path.exists():
            raise BadRequestError("site/sidebars.ts 不存在，无法同步 docs 侧边栏。", code="sidebars_missing")

        content = settings.sidebars_path.read_text(encoding="utf-8")
        if doc_id in self.parser.registered_doc_ids_from_content(content):
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
        updated = self.placement.insert_doc_with_categories(content, doc_id, category_path, labels)
        settings.sidebars_path.write_text(updated, encoding="utf-8")

    def ensure_doc_id_in_existing_category(self, doc_id: str, category_labels: list[str]) -> None:
        """把 doc_id 写入已有分类块；分类块不存在时不隐式创建。"""
        if not settings.sidebars_path.exists():
            raise BadRequestError("site/sidebars.ts 不存在，无法同步 docs 侧边栏。", code="sidebars_missing")

        content = settings.sidebars_path.read_text(encoding="utf-8")
        if doc_id in self.parser.registered_doc_ids_from_content(content):
            return

        if not category_labels:
            updated = self.placement.insert_into_first_sidebar(content, f"'{doc_id}',")
            settings.sidebars_path.write_text(updated, encoding="utf-8")
            return

        block = self.parser.find_nested_category_block(content, category_labels)
        if block is None:
            raise BadRequestError(
                "目标 docs 分类在 sidebars.ts 中不存在，无法写入文章。",
                code="sidebar_category_missing",
                details={"doc_id": doc_id, "category_labels": category_labels},
            )

        updated = self.placement.insert_into_category_items(content, block, f"'{doc_id}',")
        settings.sidebars_path.write_text(updated, encoding="utf-8")

    def ensure_category_path(self, category_path: list[str], category_labels: list[str]) -> None:
        """确保 sidebars.ts 中存在指定 docs 分类结构。"""
        if not settings.sidebars_path.exists():
            raise BadRequestError("site/sidebars.ts 不存在，无法同步 docs 侧边栏。", code="sidebars_missing")

        normalized_path = [segment.strip() for segment in category_path if segment.strip()]
        labels = [
            (category_labels[index] if index < len(category_labels) and category_labels[index] else segment)
            for index, segment in enumerate(normalized_path)
        ]
        if not normalized_path or not labels:
            return

        content = settings.sidebars_path.read_text(encoding="utf-8")
        updated = self.placement.ensure_category_path_in_content(content, normalized_path, labels)
        if updated != content:
            settings.sidebars_path.write_text(updated, encoding="utf-8")

    def ensure_category_doc_link(self, label: str, doc_id: str) -> None:
        """确保指定分类项通过 ``link`` 指向分类目录页文档。"""
        if not settings.sidebars_path.exists():
            raise BadRequestError("site/sidebars.ts 不存在，无法同步 docs 侧边栏。", code="sidebars_missing")

        content = settings.sidebars_path.read_text(encoding="utf-8")
        block = self.parser.find_category_block(content, label)
        if block is None:
            raise BadRequestError(
                "目标 docs 分类在 sidebars.ts 中不存在，无法写入分类目录页链接。",
                code="sidebar_category_missing",
                details={"label": label, "doc_id": doc_id},
            )

        block_text = content[block[0] : block[1]]
        field_indent = self.parser.category_field_indent(block_text)
        if re.search(rf"^{re.escape(field_indent)}link\s*:", block_text, re.MULTILINE):
            return

        updated = self.placement.insert_category_doc_link(content, block, doc_id)
        settings.sidebars_path.write_text(updated, encoding="utf-8")
