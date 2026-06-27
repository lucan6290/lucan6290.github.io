from __future__ import annotations

from pathlib import Path

import pytest

from blog_admin.core.errors import InvalidPathError
from blog_admin.modules.content.repository import PostRepository


def _make_repository(tmp_path: Path) -> PostRepository:
    blog_root = tmp_path / "blog-content"
    posts_dir = blog_root / "source" / "_posts"
    posts_dir.mkdir(parents=True)
    (blog_root / "_config.yml").write_text(
        "category_map:\n  技术研习: tech-study\n  Python: python\n",
        encoding="utf-8",
    )
    return PostRepository(posts_dir=posts_dir, blog_root=blog_root)


def test_post_repository_rejects_path_traversal(tmp_path: Path) -> None:
    repository = _make_repository(tmp_path)

    with pytest.raises(InvalidPathError):
        repository.resolve_path("../outside.md")


def test_post_repository_parses_post_summary_with_category_map(tmp_path: Path) -> None:
    repository = _make_repository(tmp_path)
    article = repository.posts_dir / "tech-study" / "ts-python-demo.md"
    article.parent.mkdir()
    article.write_text(
        """---
title: Python 测试
date: 2026-06-26 10:00:00
categories:
  - [技术研习, Python]
tags:
  - pytest
status: published
---

正文
""",
        encoding="utf-8",
    )

    summary = repository.parse_post_summary("tech-study/ts-python-demo.md")

    assert summary is not None
    assert summary["title"] == "Python 测试"
    assert summary["category"] == "tech-study"
    assert summary["subCategory"] == "python"
    assert summary["tags"] == ["pytest"]
    assert summary["status"] == "published"


def test_post_repository_delete_removes_asset_folder(tmp_path: Path) -> None:
    repository = _make_repository(tmp_path)
    article = repository.posts_dir / "tech-study" / "ts-python-demo.md"
    asset_folder = repository.posts_dir / "tech-study" / "ts-python-demo"
    article.parent.mkdir()
    article.write_text("---\ntitle: Demo\n---\n", encoding="utf-8")
    asset_folder.mkdir()
    (asset_folder / "img1.png").write_bytes(b"image")

    repository.delete("tech-study/ts-python-demo.md")

    assert not article.exists()
    assert not asset_folder.exists()

