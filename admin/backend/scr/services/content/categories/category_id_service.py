"""Category ID encoding helpers."""

from __future__ import annotations

import base64

from scr.core.exceptions import BadRequestError
from scr.models.article import ArticleType


class CategoryIdService:
    """Encode/decode public category IDs."""

    @staticmethod
    def encode(article_type: ArticleType, path: list[str]) -> str:
        raw = f"{article_type.value}:{'/'.join(path)}"
        return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")

    @staticmethod
    def decode(category_id: str) -> tuple[ArticleType, list[str]]:
        padding = "=" * (-len(category_id) % 4)
        try:
            raw = base64.urlsafe_b64decode(f"{category_id}{padding}").decode("utf-8")
            type_text, path_text = raw.split(":", 1)
            article_type = ArticleType(type_text)
        except (ValueError, UnicodeDecodeError) as exc:
            raise BadRequestError("分类 ID 无效。", code="category_id_invalid") from exc
        return article_type, [part for part in path_text.split("/") if part]
