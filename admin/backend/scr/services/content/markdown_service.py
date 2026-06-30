"""Markdown 解析与组装服务。

- parse：将文章原始内容拆分为 Front Matter（YAML）与正文，并收集结构性校验问题；
- compose：将 frontmatter 与正文重新拼回带 Front Matter 的完整文本，用于写入文件。
"""

from dataclasses import dataclass, field
from typing import Any

import yaml

from scr.schemas.article import ValidationIssueDTO


@dataclass(frozen=True)
class ParsedMarkdown:
    """Markdown 解析结果。"""

    frontmatter: dict[str, Any]  # 解析后的 Front Matter 键值对象，失败时为空 dict
    body: str  # 去除 Front Matter 后的正文
    raw_content: str  # 原始完整内容，便于回显编辑
    issues: list[ValidationIssueDTO] = field(default_factory=list)  # 解析阶段发现的问题


class MarkdownService:
    """Markdown 内容解析器与组装器。"""

    delimiter = "---"  # Front Matter 起止分隔符

    def compose(self, frontmatter: dict[str, Any], body: str) -> str:
        """将 frontmatter 序列化为 YAML 并与正文拼装为完整的 markdown 文本。

        保留键顺序、允许 Unicode、使用块样式；正文为空时仅输出 Front Matter。
        """
        yaml_text = yaml.safe_dump(
            frontmatter,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        ).strip()
        normalized_body = body.strip()

        if normalized_body:
            return f"{self.delimiter}\n{yaml_text}\n{self.delimiter}\n\n{normalized_body}\n"
        return f"{self.delimiter}\n{yaml_text}\n{self.delimiter}\n\n"

    def parse(self, raw_content: str) -> ParsedMarkdown:
        """解析原始内容，返回 frontmatter / body / 问题列表。

        对缺省 Front Matter、未闭合、非键值对象、YAML 语法错误等情形分别记录对应问题。
        """
        # 统一换行符并兼容旧文章中的 UTF-8 BOM，避免干扰 Front Matter 分隔符匹配
        normalized = raw_content.lstrip("\ufeff").replace("\r\n", "\n")

        # 必须以 `---\n` 开头才视为含 Front Matter
        if not normalized.startswith(f"{self.delimiter}\n"):
            return ParsedMarkdown(
                frontmatter={},
                body=normalized,
                raw_content=normalized,
                issues=[
                    ValidationIssueDTO(
                        code="frontmatter_missing",
                        message="文件顶部缺少 Front Matter。",
                    )
                ],
            )

        # 查找闭合分隔符（前面带换行，避免与起始分隔符误匹配）
        closing_index = normalized.find(f"\n{self.delimiter}\n", len(self.delimiter) + 1)
        if closing_index == -1:
            return ParsedMarkdown(
                frontmatter={},
                body=normalized,
                raw_content=normalized,
                issues=[
                    ValidationIssueDTO(
                        code="frontmatter_not_closed",
                        message="Front Matter 缺少结束分隔符。",
                        severity="error",
                    )
                ],
            )

        yaml_text = normalized[len(self.delimiter) + 1 : closing_index]
        body = normalized[closing_index + len(self.delimiter) + 2 :]
        issues: list[ValidationIssueDTO] = []

        try:
            loaded = yaml.safe_load(yaml_text) or {}
            if not isinstance(loaded, dict):
                # Front Matter 必须是键值对象，例如不能是纯列表或标量
                loaded = {}
                issues.append(
                    ValidationIssueDTO(
                        code="frontmatter_not_mapping",
                        message="Front Matter 必须是键值对象。",
                        severity="error",
                    )
                )
        except yaml.YAMLError as exc:
            loaded = {}
            issues.append(
                ValidationIssueDTO(
                    code="frontmatter_yaml_error",
                    message=f"Front Matter YAML 解析失败：{exc}",
                    severity="error",
                )
            )

        return ParsedMarkdown(
            frontmatter=loaded,
            body=body,
            raw_content=normalized,
            issues=issues,
        )
