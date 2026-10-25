"""Category path validation helpers."""

from __future__ import annotations

from scr.core.exceptions import BadRequestError


class CategoryPathService:
    """Normalize and validate category path segments."""

    @staticmethod
    def normalize_path(path: list[str]) -> list[str]:
        normalized = [segment.strip() for segment in path if segment.strip()]
        if not normalized:
            raise BadRequestError("分类路径不能为空。", code="category_path_empty")
        for segment in normalized:
            CategoryPathService.validate_slug(segment)
        return normalized

    @staticmethod
    def validate_slug(slug: str) -> None:
        if slug in {".", ".."} or "/" in slug or "\\" in slug or not slug.strip():
            raise BadRequestError(
                "目标分类 slug 不合法。",
                code="invalid_category_slug",
                details={"target_slug": slug},
            )
