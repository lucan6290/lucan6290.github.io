"""Front matter validation for article files."""

from __future__ import annotations

import re
from typing import Any

from scr.schemas.article import ValidationIssueDTO


class ArticleFrontmatterValidationService:
    """Validate docs and blog front matter fields."""

    date_prefix_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}")
    unsafe_path_segment_pattern = re.compile(r'[<>:"\\|?*\x00-\x1f/]')

    def validate_docs(self, frontmatter: dict[str, Any], sidebar_registered: bool) -> list[ValidationIssueDTO]:
        issues: list[ValidationIssueDTO] = []

        if not frontmatter.get("title"):
            issues.append(
                ValidationIssueDTO(
                    code="docs_title_missing",
                    message="docs 文章缺少 title。",
                    severity="error",
                )
            )
        if not frontmatter.get("description"):
            issues.append(
                ValidationIssueDTO(
                    code="docs_description_missing",
                    message="docs 文章建议填写 description。",
                )
            )
        if not sidebar_registered:
            issues.append(
                ValidationIssueDTO(
                    code="docs_sidebar_missing",
                    message="docs 文章尚未登记到 site/sidebars.ts。",
                    severity="error",
                )
            )

        return issues

    def validate_blog(self, frontmatter: dict[str, Any], known_authors: set[str]) -> list[ValidationIssueDTO]:
        issues: list[ValidationIssueDTO] = []

        required_fields = ["title", "slug", "authors", "date", "last_update"]
        for field_name in required_fields:
            if not frontmatter.get(field_name):
                issues.append(
                    ValidationIssueDTO(
                        code=f"blog_{field_name}_missing",
                        message=f"blog 文章缺少 {field_name}。",
                        severity="error",
                    )
                )

        slug = self.string_value(frontmatter.get("slug"))
        if slug and not self.is_safe_path_segment(slug):
            issues.append(
                ValidationIssueDTO(
                    code="blog_slug_invalid",
                    message="blog slug 不能包含路径危险字符。",
                    severity="error",
                )
            )

        if not frontmatter.get("description"):
            issues.append(
                ValidationIssueDTO(
                    code="blog_description_missing",
                    message="blog 文章建议填写 description。",
                )
            )

        if "tags" not in frontmatter:
            issues.append(
                ValidationIssueDTO(
                    code="blog_tags_missing",
                    message="blog 文章建议保留 tags 字段，允许为空数组。",
                )
            )

        date_value = self.string_value(frontmatter.get("date"))
        if date_value and not self.date_prefix_pattern.match(date_value):
            issues.append(
                ValidationIssueDTO(
                    code="blog_date_invalid",
                    message="blog date 必须以 YYYY-MM-DD 开头。",
                    severity="error",
                )
            )

        last_update = frontmatter.get("last_update")
        if last_update and not isinstance(last_update, dict):
            issues.append(
                ValidationIssueDTO(
                    code="blog_last_update_invalid",
                    message="blog last_update 必须是包含 date/author 的对象。",
                    severity="error",
                )
            )
        elif isinstance(last_update, dict):
            if not self.string_value(last_update.get("date")):
                issues.append(
                    ValidationIssueDTO(
                        code="blog_last_update_date_missing",
                        message="blog last_update 缺少 date。",
                        severity="error",
                    )
                )
            if not self.string_value(last_update.get("author")):
                issues.append(
                    ValidationIssueDTO(
                        code="blog_last_update_author_missing",
                        message="blog last_update 缺少 author。",
                        severity="error",
                    )
                )

        for author in self.list_value(frontmatter.get("authors")):
            if author not in known_authors:
                issues.append(
                    ValidationIssueDTO(
                        code="blog_author_unknown",
                        message=f"blog 作者 {author} 不存在于 site/blog/authors.yml。",
                        severity="error",
                    )
                )

        return issues

    @staticmethod
    def string_value(value: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    @staticmethod
    def list_value(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        return [str(value)]

    @classmethod
    def is_safe_path_segment(cls, value: str) -> bool:
        normalized = value.strip()
        return bool(
            normalized
            and normalized not in {".", ".."}
            and not cls.unsafe_path_segment_pattern.search(normalized)
            and not normalized.endswith((".", " "))
        )
