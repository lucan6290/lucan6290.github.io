from pathlib import Path

import pytest

from scr.core.config import settings
from scr.core.exceptions import NotFoundError
from scr.models.article import ArticleType
from scr.schemas.article import ArticleCreateDTO, ArticleMoveDTO
from scr.schemas.category import CategoryCreateDTO
from scr.services.content.articles.article_service import ArticleService
from scr.services.content.categories.category_service import CategoryService
from scr.application.content.workflows.article_workflow import ArticleWorkflowService


def _set_temp_content_root(tmp_path: Path) -> dict[str, Path]:
    project_root = tmp_path
    site_dir = project_root / "site"
    paths = {
        "project_root": project_root,
        "site_dir": site_dir,
        "docs_dir": site_dir / "docs",
        "blog_dir": site_dir / "blog",
        "sidebars_path": site_dir / "sidebars.ts",
        "docusaurus_config_path": site_dir / "docusaurus.config.ts",
        "content_schema_dir": project_root / "admin" / "backend" / "data" / "content-schema",
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


def _knowledge_config() -> str:
    return """export default {
  themeConfig: {
    navbar: {
      items: [
        {
          type: 'dropdown',
          label: '知识库',
          items: [],
        },
      ],
    },
  },
};
"""


def _empty_sidebars() -> str:
    return "const sidebars = {\n};\nexport default sidebars;\n"


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
        settings.docusaurus_config_path.write_text(
            "export default { themeConfig: { navbar: { items: [{ to: '/docs/topic/old' }] } } };",
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
        assert "/docs/topic/old" in settings.docusaurus_config_path.read_text(encoding="utf-8")
        assert "/docs/topic/new" not in settings.docusaurus_config_path.read_text(encoding="utf-8")
        assert any(change.description == "已更新文章内图片目录引用" for change in plan.changes)
        assert not any("顶部导航" in change.description for change in plan.changes)
    finally:
        _restore_settings(original)


def test_create_docs_article_requires_existing_category(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        settings.sidebars_path.write_text("const sidebars = { docs: [] };\nexport default sidebars;\n", encoding="utf-8")
        settings.docusaurus_config_path.write_text(
            "export default { themeConfig: { navbar: { items: [] } } };\n",
            encoding="utf-8",
        )

        service = ArticleService()
        workflow = ArticleWorkflowService(service)
        with pytest.raises(NotFoundError):
            workflow.create_article(
                ArticleCreateDTO(
                    type=ArticleType.docs,
                    title="Java vs C++",
                    slug="java-vs-cpp",
                    category_path=["tech-study", "java-basic"],
                    body="Body",
                )
            )

        assert not (settings.docs_dir / "tech-study").exists()
        assert "tech-study" not in settings.docusaurus_config_path.read_text(encoding="utf-8")
    finally:
        _restore_settings(original)


def test_create_docs_article_appends_to_existing_sidebar_category(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        settings.docusaurus_config_path.write_text(_knowledge_config(), encoding="utf-8")
        settings.sidebars_path.write_text(_empty_sidebars(), encoding="utf-8")

        category_service = CategoryService()
        category_service.create_category(CategoryCreateDTO(type=ArticleType.docs, path=["resource-sharing"], label="资源分享"))
        category_service.create_category(
            CategoryCreateDTO(type=ArticleType.docs, path=["resource-sharing", "接口测试1"], label="接口测试1")
        )

        ArticleWorkflowService(ArticleService()).create_article(
            ArticleCreateDTO(
                type=ArticleType.docs,
                title="测试",
                slug="测试",
                category_path=["resource-sharing", "接口测试1"],
                body="Body",
            )
        )

        sidebars = settings.sidebars_path.read_text(encoding="utf-8")
        assert "'resource-sharingSidebar': [" in sidebars
        assert "label: '资源分享'" in sidebars
        assert "label: '接口测试1'" in sidebars
        assert "'resource-sharing/接口测试1/测试'" in sidebars
        assert sidebars.count("label: '接口测试1'") == 1
    finally:
        _restore_settings(original)


def test_create_blog_article_uses_top_level_category_without_date_prefix(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        (settings.blog_dir / "authors.yml").write_text("lucan:\n  name: Lucan\n", encoding="utf-8")

        detail = ArticleWorkflowService(ArticleService()).create_article(
            ArticleCreateDTO(
                type=ArticleType.blog,
                title="AI编程工具的真实体验：强但没那么神",
                slug="AI编程工具真实体验",
                category_path=["AI观察"],
                authors=["lucan"],
                date="2026-06-04T11:04:59+08:00",
                description="企业级项目中使用 AI 编程工具的真实体验。",
                tags=[],
                body="Body",
            )
        )

        article_path = settings.blog_dir / "AI观察" / "AI编程工具真实体验.md"
        assert article_path.exists()
        assert not (settings.blog_dir / "2026-06-04-AI编程工具真实体验.md").exists()
        assert detail.relative_path == "AI观察/AI编程工具真实体验.md"
        assert detail.category_path == ["AI观察"]
        assert detail.route == "/blog/AI编程工具真实体验"
        assert detail.frontmatter["slug"] == "AI编程工具真实体验"
        assert detail.frontmatter["date"] == "2026-06-04T11:04:59+08:00"
        assert detail.frontmatter["last_update"] == {
            "date": "2026-06-04T11:04:59+08:00",
            "author": "lucan",
        }
        assert detail.frontmatter["tags"] == []

        categories = CategoryService().list_categories(
            article_type=ArticleType.blog,
            include_empty=False,
            include_counts=True,
        )
        assert len(categories) == 1
        assert categories[0].path == ["AI观察"]
        assert categories[0].article_count == 1
    finally:
        _restore_settings(original)


def test_blog_articles_sort_by_frontmatter_date(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        (settings.blog_dir / "随笔感想").mkdir(parents=True)
        (settings.blog_dir / "随笔感想" / "晚发布.md").write_text(
            "---\n"
            "slug: 晚发布\n"
            "title: 晚发布\n"
            "authors: lucan\n"
            "date: 2026-07-01T10:00:00+08:00\n"
            "last_update:\n"
            "  date: 2026-07-01T10:00:00+08:00\n"
            "  author: lucan\n"
            "description: late\n"
            "tags: []\n"
            "---\n\nBody\n",
            encoding="utf-8",
        )
        (settings.blog_dir / "随笔感想" / "早发布.md").write_text(
            "---\n"
            "slug: 早发布\n"
            "title: 早发布\n"
            "authors: lucan\n"
            "date: 2026-01-01T10:00:00+08:00\n"
            "last_update:\n"
            "  date: 2026-01-01T10:00:00+08:00\n"
            "  author: lucan\n"
            "description: early\n"
            "tags: []\n"
            "---\n\nBody\n",
            encoding="utf-8",
        )

        items = ArticleService().list_articles(article_type=ArticleType.blog, sort="-date").items

        assert [item.slug for item in items] == ["晚发布", "早发布"]
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


def test_move_blog_article_between_top_level_categories(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        (settings.blog_dir / "authors.yml").write_text("lucan:\n  name: Lucan\n", encoding="utf-8")
        service = ArticleService()
        detail = ArticleWorkflowService(service).create_article(
            ArticleCreateDTO(
                type=ArticleType.blog,
                title="旧标题",
                slug="旧标题",
                category_path=["随笔感想"],
                authors=["lucan"],
                date="2026-07-01T10:00:00+08:00",
                description="desc",
                body="Body",
            )
        )

        service.move_article(
            detail.id,
            ArticleMoveDTO(
                target_type=ArticleType.blog,
                target_slug="新标题",
                target_category_path=["成长随笔"],
                dry_run=False,
                confirm=True,
            ),
        )

        assert not (settings.blog_dir / "随笔感想" / "旧标题.md").exists()
        moved = settings.blog_dir / "成长随笔" / "新标题.md"
        assert moved.exists()
        assert "slug: 新标题" in moved.read_text(encoding="utf-8")
        moved_detail = service.get_article(service.encode_article_id(ArticleType.blog, "成长随笔/新标题.md"))
        assert moved_detail.category_path == ["成长随笔"]
        assert moved_detail.route == "/blog/新标题"
    finally:
        _restore_settings(original)


def test_move_docs_article_between_categories_repositions_sidebar_item(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        settings.docusaurus_config_path.write_text(_knowledge_config(), encoding="utf-8")
        settings.sidebars_path.write_text(_empty_sidebars(), encoding="utf-8")

        category_service = CategoryService()
        category_service.create_category(CategoryCreateDTO(type=ArticleType.docs, path=["resource-sharing"], label="资源分享"))
        category_service.create_category(
            CategoryCreateDTO(type=ArticleType.docs, path=["resource-sharing", "接口测试1"], label="接口测试1")
        )
        category_service.create_category(
            CategoryCreateDTO(type=ArticleType.docs, path=["resource-sharing", "接口测试2"], label="接口测试2")
        )

        article = settings.docs_dir / "resource-sharing" / "接口测试1" / "测试.md"
        article.parent.mkdir(parents=True, exist_ok=True)
        article.write_text("---\ntitle: 测试\n---\n\nBody\n", encoding="utf-8")
        settings.sidebars_path.write_text(
            settings.sidebars_path.read_text(encoding="utf-8").replace(
                "items: [\n          ],",
                "items: [\n            'resource-sharing/接口测试1/测试',\n          ],",
                1,
            ),
            encoding="utf-8",
        )

        service = ArticleService()
        service.move_article(
            service.encode_article_id(ArticleType.docs, "resource-sharing/接口测试1/测试.md"),
            ArticleMoveDTO(
                target_type=ArticleType.docs,
                target_slug="测试",
                target_category_path=["resource-sharing", "接口测试2"],
                dry_run=False,
                confirm=True,
            ),
        )

        sidebars = settings.sidebars_path.read_text(encoding="utf-8")
        assert "resource-sharing/接口测试1/测试" not in sidebars
        assert "resource-sharing/接口测试2/测试" in sidebars
        assert sidebars.index("label: '接口测试2'") < sidebars.index("'resource-sharing/接口测试2/测试'")
    finally:
        _restore_settings(original)


def test_delete_article_ignores_top_nav_references_route(tmp_path: Path) -> None:
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
        settings.docusaurus_config_path.write_text(
            "export default { themeConfig: { navbar: { items: [{ to: '/docs/topic/old' }] } } };",
            encoding="utf-8",
        )
        old_article = settings.docs_dir / "topic" / "old.md"
        old_article.parent.mkdir(parents=True, exist_ok=True)
        old_article.write_text("---\ntitle: Old\n---\n\nBody\n", encoding="utf-8")

        service = ArticleService()
        article_id = service.encode_article_id(ArticleType.docs, "topic/old.md")
        plan = service.delete_article(article_id, dry_run=True)

        assert not any("docusaurus.config.ts" in warning for warning in plan.warnings)
    finally:
        _restore_settings(original)
