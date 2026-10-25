"""Blog author registry helpers."""

from __future__ import annotations

from typing import Any

import yaml

from scr.core.config import settings
from scr.core.exceptions import BadRequestError


class BlogAuthorService:
    """Read and validate site/blog/authors.yml authors."""

    def load_authors(self) -> set[str]:
        authors_path = settings.blog_dir / "authors.yml"
        if not authors_path.exists():
            return set()

        try:
            loaded = yaml.safe_load(authors_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            return set()

        if not isinstance(loaded, dict):
            return set()

        return set(str(author_id) for author_id in loaded)

    def validate_authors(self, authors: list[str]) -> None:
        known_authors = self.load_authors()
        unknown_authors = [author for author in authors if author not in known_authors]
        if unknown_authors:
            raise BadRequestError(
                "blog 作者不存在于 site/blog/authors.yml。",
                code="blog_author_unknown",
                details={"authors": unknown_authors},
            )

    def last_update_author(self, frontmatter: dict[str, Any]) -> str:
        last_update = frontmatter.get("last_update")
        if isinstance(last_update, dict):
            author = self._string_value(last_update.get("author"))
            if author:
                return author
        return self.first_author(self._list_value(frontmatter.get("authors")))

    @staticmethod
    def first_author(authors: list[str]) -> str:
        for author in authors:
            normalized = author.strip()
            if normalized:
                return normalized
        return "lucan"

    @staticmethod
    def _string_value(value: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    @staticmethod
    def _list_value(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        return [str(value)]
