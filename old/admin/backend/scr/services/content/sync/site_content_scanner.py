"""Scan actual site content without reading admin registry files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Iterable

from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.filesystem.markdown_service import MarkdownService
from scr.models.article import ArticleType


@dataclass(frozen=True)
class SiteArticleSnapshot:
    """An article discovered from ``site/docs`` or ``site/blog``."""

    type: ArticleType
    path: Path
    relative_path: str
    doc_id: str
    title: str
    slug: str
    date: str
    category_path: tuple[str, ...]
    is_index: bool = False


@dataclass(frozen=True)
class SiteCategorySnapshot:
    """A category path inferred from real content directories."""

    type: ArticleType
    path: tuple[str, ...]
    label: str
    article_count: int = 0
    has_index: bool = False
    has_title: bool = False  # label 是否来自 index.md 的 title（否则为目录名兜底）


@dataclass(frozen=True)
class SiteContentSnapshot:
    """Combined docs/blog content snapshot."""

    docs_articles: tuple[SiteArticleSnapshot, ...] = ()
    blog_articles: tuple[SiteArticleSnapshot, ...] = ()
    docs_categories: tuple[SiteCategorySnapshot, ...] = ()
    blog_categories: tuple[SiteCategorySnapshot, ...] = ()

    @property
    def articles(self) -> tuple[SiteArticleSnapshot, ...]:
        return (*self.docs_articles, *self.blog_articles)

    @property
    def categories(self) -> tuple[SiteCategorySnapshot, ...]:
        return (*self.docs_categories, *self.blog_categories)


class SiteContentScanner:
    """Build a deterministic snapshot from actual ``site/docs`` and ``site/blog`` files."""

    _blog_date_prefix_re = re.compile(r"^\d{4}-\d{2}-\d{2}-")

    def __init__(self) -> None:
        self.filesystem = FileSystemService()
        self.markdown = MarkdownService()

    def scan(self) -> SiteContentSnapshot:
        """Scan both supported content roots."""
        docs_articles = tuple(self._scan_articles(ArticleType.docs))
        blog_articles = tuple(self._scan_articles(ArticleType.blog))
        return SiteContentSnapshot(
            docs_articles=docs_articles,
            blog_articles=blog_articles,
            docs_categories=tuple(self._build_categories(ArticleType.docs, docs_articles)),
            blog_categories=tuple(self._build_categories(ArticleType.blog, blog_articles)),
        )

    def _scan_articles(self, article_type: ArticleType) -> list[SiteArticleSnapshot]:
        articles: list[SiteArticleSnapshot] = []
        for path in self.filesystem.scan_article_files(article_type):
            relative_path = self.filesystem.relative_posix_path(article_type, path)
            parts = [part for part in relative_path.split("/") if part]
            if not parts:
                continue

            parsed = self.markdown.parse(path.read_text(encoding="utf-8"))
            frontmatter = parsed.frontmatter
            stem = path.stem
            is_index = stem.lower() == "index"
            category_path = tuple(parts[:-1])
            doc_id = relative_path.rsplit(".", 1)[0]
            slug = str(frontmatter.get("slug") or "").strip().lstrip("/")
            if not slug:
                slug = self._slug_from_filename(path.name) if article_type == ArticleType.blog else stem

            title = str(frontmatter.get("title") or "").strip()
            if not title:
                title = category_path[-1] if is_index and category_path else stem

            articles.append(
                SiteArticleSnapshot(
                    type=article_type,
                    path=path,
                    relative_path=relative_path,
                    doc_id=doc_id,
                    title=title,
                    slug=slug,
                    date=str(frontmatter.get("date") or ""),
                    category_path=category_path,
                    is_index=is_index,
                )
            )
        return articles

    def _build_categories(
        self,
        article_type: ArticleType,
        articles: Iterable[SiteArticleSnapshot],
    ) -> list[SiteCategorySnapshot]:
        labels: dict[tuple[str, ...], str] = {}
        counts: dict[tuple[str, ...], int] = {}
        has_index: set[tuple[str, ...]] = set()
        title_paths: set[tuple[str, ...]] = set()

        for article in articles:
            if not article.category_path:
                continue
            for depth in range(1, len(article.category_path) + 1):
                path = article.category_path[:depth]
                labels.setdefault(path, self._default_label(path[-1]))
                counts.setdefault(path, 0)
            if article.is_index:
                has_index.add(article.category_path)
                if article.title:
                    labels[article.category_path] = article.title
                    title_paths.add(article.category_path)
                else:
                    labels.setdefault(article.category_path, self._default_label(article.category_path[-1]))
            else:
                counts[article.category_path] = counts.get(article.category_path, 0) + 1

        return [
            SiteCategorySnapshot(
                type=article_type,
                path=path,
                label=labels.get(path) or self._default_label(path[-1]),
                article_count=counts.get(path, 0),
                has_index=path in has_index,
                has_title=path in title_paths,
            )
            for path in sorted(labels, key=lambda item: (len(item), "/".join(item)))
        ]

    @classmethod
    def _slug_from_filename(cls, filename: str) -> str:
        return cls._blog_date_prefix_re.sub("", Path(filename).stem, count=1)

    @staticmethod
    def _default_label(value: str) -> str:
        return value.replace("-", " ").replace("_", " ").strip() or value
