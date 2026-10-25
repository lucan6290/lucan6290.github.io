"""Article path and category-path rules."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from scr.core.exceptions import BadRequestError
from scr.models.article import ArticleType


class ArticlePathService:
    """Validate article path segments and derive category paths."""

    unsafe_path_segment_pattern = re.compile(r'[<>:"\\|?*\x00-\x1f/]')

    def validate_path_segment(self, value: str, *, field_name: str) -> None:
        if not self.is_safe_path_segment(value):
            raise BadRequestError(
                "路径片段不能为空，不能使用 . 或 ..，且不能包含 /、\\、:、*、?、\"、<、>、| 等字符。",
                code="invalid_path_segment",
                details={"field": field_name, "value": value},
            )

    def validate_docs_category_path(self, category_path: list[str]) -> None:
        invalid_segments = [segment for segment in category_path if not self.is_safe_path_segment(segment)]
        if invalid_segments:
            raise BadRequestError(
                "docs 目标分类片段不合法。",
                code="invalid_target_category",
                details={"target_category_path": category_path, "invalid_segments": invalid_segments},
            )

    def validate_blog_category_path(self, category_path: list[str]) -> None:
        if len(category_path) != 1 or not self.is_safe_path_segment(category_path[0]):
            raise BadRequestError(
                "blog 文章必须选择且只能选择一个一级分类。",
                code="invalid_blog_category",
                details={"category_path": category_path},
            )

    def is_safe_path_segment(self, value: str) -> bool:
        normalized = value.strip()
        return bool(
            normalized
            and normalized not in {".", ".."}
            and not self.unsafe_path_segment_pattern.search(normalized)
            and not normalized.endswith((".", " "))
        )

    @staticmethod
    def category_path(article_type: ArticleType, relative_path: str, frontmatter: dict[str, Any]) -> list[str]:
        parts = Path(relative_path).parent.as_posix().split("/")
        if parts == ["."]:
            return []
        if article_type == ArticleType.blog:
            return parts[:1]
        return parts

    @staticmethod
    def string_value(value: Any) -> str | None:
        if value is None:
            return None
        return str(value)
