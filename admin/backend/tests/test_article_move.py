from pathlib import Path

from scr.core.config import settings
from scr.models.article import ArticleType
from scr.schemas.article import ArticleMoveDTO
from scr.services.content.article_service import ArticleService


def _set_temp_content_root(tmp_path: Path) -> dict[str, Path]:
    project_root = tmp_path
    site_dir = project_root / "site"
    paths = {
        "project_root": project_root,
        "site_dir": site_dir,
        "docs_dir": site_dir / "docs",
        "blog_dir": site_dir / "blog",
        "sidebars_path": site_dir / "sidebars.ts",
    }
    for path in paths.values():
        if path.suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            path.mkdir(parents=True, exist_ok=True)

    original = {name: getattr(settings, name) for name in paths}
    for name, path in paths.items():
        object.__setattr__(settings, name, path)
    return original


def _restore_settings(original: dict[str, Path]) -> None:
    for name, path in original.items():
        object.__setattr__(settings, name, path)


def test_move_docs_article_syncs_related_files(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        settings.sidebars_path.write_text(
            """const sidebars = {
  docs: [
    'topic/old',
  ],
};
export default sidebars;
""",
            encoding="utf-8",
        )
        old_article = settings.docs_dir / "topic" / "old.md"
        old_article.parent.mkdir(parents=True, exist_ok=True)
        old_article.write_text(
            """---
title: Old
---

![cover](./old-imgs/cover.png)
""",
            encoding="utf-8",
        )
        image_dir = old_article.with_name("old-imgs")
        image_dir.mkdir()
        (image_dir / "cover.png").write_bytes(b"image")

        linker = settings.docs_dir / "linker.md"
        linker.write_text("See /docs/topic/old and topic/old.md", encoding="utf-8")

        service = ArticleService()
        article_id = service.encode_article_id(ArticleType.docs, "topic/old.md")
        plan = service.move_article(
            article_id,
            ArticleMoveDTO(
                target_type=ArticleType.docs,
                target_slug="new",
                target_category_path=["topic"],
                replace_links=True,
                dry_run=False,
                confirm=True,
            ),
        )

        new_article = settings.docs_dir / "topic" / "new.md"
        new_image_dir = new_article.with_name("new-imgs")
        assert not old_article.exists()
        assert new_article.exists()
        assert not image_dir.exists()
        assert (new_image_dir / "cover.png").exists()
        assert "./new-imgs/cover.png" in new_article.read_text(encoding="utf-8")
        assert "topic/new" in settings.sidebars_path.read_text(encoding="utf-8")
        assert "topic/old" not in settings.sidebars_path.read_text(encoding="utf-8")
        assert "/docs/topic/new" in linker.read_text(encoding="utf-8")
        assert any(change.description == "已更新文章内图片目录引用" for change in plan.changes)
    finally:
        _restore_settings(original)


def test_move_docs_article_allows_root_category(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        settings.sidebars_path.write_text(
            """const sidebars = {
  docs: [
    'old',
  ],
};
export default sidebars;
""",
            encoding="utf-8",
        )
        old_article = settings.docs_dir / "old.md"
        old_article.write_text("---\ntitle: Old\n---\n\nRoot article\n", encoding="utf-8")

        service = ArticleService()
        article_id = service.encode_article_id(ArticleType.docs, "old.md")
        service.move_article(
            article_id,
            ArticleMoveDTO(
                target_type=ArticleType.docs,
                target_slug="new",
                target_category_path=[],
                dry_run=False,
                confirm=True,
            ),
        )

        assert not old_article.exists()
        assert (settings.docs_dir / "new.md").exists()
        assert "'new'" in settings.sidebars_path.read_text(encoding="utf-8")
    finally:
        _restore_settings(original)
