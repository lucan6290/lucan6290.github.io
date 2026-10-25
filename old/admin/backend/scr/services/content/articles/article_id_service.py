"""Article ID encoding helpers."""

from __future__ import annotations

import base64

from scr.core.exceptions import NotFoundError
from scr.models.article import ArticleType


class ArticleIdService:
    """Encode/decode public article IDs."""

    @staticmethod
    def encode(article_type: ArticleType, relative_path: str) -> str:
        raw = f"{article_type.value}:{relative_path}"
        return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")

    @staticmethod
    def decode(article_id: str) -> tuple[ArticleType, str]:
        padding = "=" * (-len(article_id) % 4)
        try:
            raw = base64.urlsafe_b64decode(f"{article_id}{padding}").decode("utf-8")
            type_text, relative_path = raw.split(":", 1)
            return ArticleType(type_text), relative_path
        except (ValueError, UnicodeDecodeError) as exc:
            raise NotFoundError("文章 ID 无效。", code="article_id_invalid") from exc
