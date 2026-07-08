from pathlib import Path

import sqlite3
import pytest

from scr.core.config import settings
from scr.models.article import ArticleType
from scr.schemas.article import ArticleCreateDTO, ArticleMoveDTO
from scr.schemas.category import CategoryCreateDTO, CategoryRenameDTO, CategoryUpdateDTO
from scr.schemas.docusaurus_config import DocusaurusConfigSyncDTO
from scr.schemas.sidebar import SidebarSyncDTO
from scr.services.content.articles.article_service import ArticleService
from scr.services.content.blog.blog_index_service import BlogIndexService
from scr.services.content.categories.category_id_service import CategoryIdService
from scr.services.content.categories.category_service import CategoryService
from scr.services.content.docusaurus.docusaurus_config_management_service import DocusaurusConfigManagementService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.infrastructure.registry.registry_index_service import RegistryIndexService
from scr.services.content.sidebars.sidebar_management_service import SidebarManagementService
from scr.application.content.workflows.article_workflow import ArticleWorkflowService
from scr.application.content.workflows.blog_article_workflow import BlogArticleWorkflow


def _set_temp_content_root(tmp_path: Path) -> dict[str, Path]:
    project_root = tmp_path
    site_dir = project_root / "site"
    paths = {
        "project_root": project_root,
        "site_dir": site_dir,
        "docs_dir": site_dir / "docs",
        "blog_dir": site_dir / "blog",
        "sidebars_path": site_dir / "sidebars.ts",
        "blog_sidebars_path": site_dir / "blogSidebars.ts",
        "docusaurus_config_path": site_dir / "docusaurus.config.ts",
        "content_schema_dir": project_root / "admin" / "backend" / "data" / "content-schema",
        "registry_index_path": project_root / "admin" / "backend" / "data" / "registry_index.sqlite3",
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


def _config_with_blog_dropdown() -> str:
    return """export default {
  themeConfig: {
    navbar: {
      items: [
        {
          type: 'dropdown',
          label: '知识库',
          items: [],
        },
        {
          type: 'dropdown',
          label: '博客',
          position: 'left',
          items: [
            {
              label: '博客首页',
              to: '/blog',
            },
            {
              label: '旧文章链接',
              to: '/blog/旧文章',
            },
          ],
        },
      ],
    },
  },
};
"""


def _write_blog_article(path: Path, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        f"slug: {path.stem}\n"
        f"title: {title}\n"
        "authors: lucan\n"
        "date: 2026-07-01T10:00:00+08:00\n"
        "last_update:\n"
        "  date: 2026-07-01T10:00:00+08:00\n"
        "  author: lucan\n"
        "description: desc\n"
        "tags: []\n"
        "---\n\nBody\n",
        encoding="utf-8",
    )


def test_blog_sidebar_status_and_sync_categories(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        _write_blog_article(settings.blog_dir / "AI观察" / "AI编程工具真实体验.md", "AI 编程工具真实体验")
        _write_blog_article(settings.blog_dir / "随笔感想" / "一次复盘.md", "一次复盘")
        settings.blog_sidebars_path.write_text(
            """export type BlogSidebarItem = {
  label: string;
  path: string;
  to: string;
  count?: number;
  collapsed?: boolean;
};

const blogSidebars: BlogSidebarItem[] = [
  {
    label: 'AI观察',
    path: 'AI观察',
    to: '/blog/AI观察',
    count: 1,
    collapsed: true,
  },
  {
    label: '旧分类',
    path: '旧分类',
    to: '/blog/旧分类',
    count: 3,
  },
];

export default blogSidebars;
""",
            encoding="utf-8",
        )

        service = SidebarManagementService()
        status = service.get_status(type="blog")

        assert status.type == "blog"
        assert status.blog_category_count == 2
        assert status.missing_in_sidebars == ["随笔感想"]
        assert status.orphan_sidebar_ids == ["旧分类"]

        plan = service.sync(SidebarSyncDTO(type="blog", mode="sync_categories", dry_run=True))
        assert plan.dry_run is True
        assert any("追加 blog 一级分类「随笔感想」" in change.description for change in plan.changes)
        assert any("移除不存在的 blog 侧边栏分类「旧分类」" in change.description for change in plan.changes)

        service.sync(SidebarSyncDTO(type="blog", mode="sync_categories", dry_run=False, confirm=True))

        content = settings.blog_sidebars_path.read_text(encoding="utf-8")
        assert "path: 'AI观察'" in content
        assert "collapsed: true" in content
        assert "path: '随笔感想'" in content
        assert "to: '/blog/随笔感想'" in content
        assert "items: [" in content
        assert "label: 'AI 编程工具真实体验'" in content
        assert "to: '/blog/AI编程工具真实体验'" in content
        assert "path: '旧分类'" not in content
    finally:
        _restore_settings(original)


def test_docusaurus_config_syncs_blog_top_categories_to_blog_dropdown(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        _write_blog_article(settings.blog_dir / "AI观察" / "AI编程工具真实体验.md", "AI 编程工具真实体验")
        settings.docusaurus_config_path.write_text(_config_with_blog_dropdown(), encoding="utf-8")

        service = DocusaurusConfigManagementService()
        status = service.get_status()

        assert status.blog_top_category_total == 1
        assert [item.slug for item in status.blog_top_categories_missing_in_nav] == ["AI观察"]
        assert [item.to for item in status.stale_blog_nav_items] == ["/blog/旧文章"]
        assert not any(item.to == "/blog/AI观察" for item in status.broken_to_links)

        plan = service.sync(DocusaurusConfigSyncDTO(mode="append_missing_top", dry_run=True))
        assert any("追加 blog 一级分类「AI观察」到博客导航" in change.description for change in plan.changes)

        cleanup_plan = service.sync(DocusaurusConfigSyncDTO(mode="all", dry_run=True))
        assert any("移除断链导航项 to: /blog/旧文章" in change.description for change in cleanup_plan.changes)

        service.sync(DocusaurusConfigSyncDTO(mode="all", dry_run=False, confirm=True))

        config = settings.docusaurus_config_path.read_text(encoding="utf-8")
        assert "label: 'AI观察'" in config
        assert "to: '/blog/AI观察'" in config
        assert "to: '/blog/旧文章'" not in config
    finally:
        _restore_settings(original)


def test_blog_index_sync_only_writes_root_index_and_keeps_it_out_of_articles(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        _write_blog_article(settings.blog_dir / "AI观察" / "AI编程工具真实体验.md", "AI 编程工具真实体验")
        _write_blog_article(settings.blog_dir / "随笔感想" / "一次复盘.md", "一次复盘")

        service = BlogIndexService()
        plan = service.sync_all(dry_run=True)
        assert plan.dry_run is True
        assert [change.target for change in plan.changes] == ["site/blog/index.md"]

        service.sync_all(dry_run=False, confirm=True)

        assert (settings.blog_dir / "index.md").exists()
        assert not (settings.blog_dir / "AI观察" / "index.md").exists()
        assert not (settings.blog_dir / "随笔感想" / "index.md").exists()

        scanned = [
            FileSystemService().relative_posix_path(ArticleType.blog, path)
            for path in FileSystemService().scan_article_files(ArticleType.blog)
        ]
        assert scanned == ["AI观察/AI编程工具真实体验.md", "随笔感想/一次复盘.md"]
    finally:
        _restore_settings(original)


def test_create_blog_article_syncs_index_sidebar_nav_and_registry(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        settings.docusaurus_config_path.write_text(_config_with_blog_dropdown(), encoding="utf-8")
        (settings.blog_dir / "authors.yml").write_text("lucan:\n  name: lucan\n", encoding="utf-8")
        (settings.blog_dir / "tech").mkdir(parents=True, exist_ok=True)
        settings.blog_sidebars_path.write_text("const blogSidebars = [];\n\nexport default blogSidebars;\n", encoding="utf-8")
        (settings.blog_dir / "index.md").write_text(
            "# 博客\n\n这里用于整理个人表达、阶段观察、感想复盘和年度回顾。\n\n## 分类目录\n",
            encoding="utf-8",
        )

        article = ArticleWorkflowService(ArticleService()).create_article(
            ArticleCreateDTO(
                type=ArticleType.blog,
                title="新文章",
                slug="new-post",
                description="desc",
                body="Body",
                category_path=["tech"],
                authors=["lucan"],
                tags=["Docusaurus"],
                date="2026-07-02T10:00:00+08:00",
            )
        )

        assert article.relative_path == "tech/new-post.md"
        assert (settings.blog_dir / "tech" / "new-post.md").exists()

        index_content = (settings.blog_dir / "index.md").read_text(encoding="utf-8")
        assert "## 分类目录" in index_content
        assert "### [Tech](/blog/tech)" in index_content
        assert "- [新文章](/blog/new-post)" in index_content
        assert "最新文章" not in index_content
        assert "---" not in index_content

        sidebar_content = settings.blog_sidebars_path.read_text(encoding="utf-8")
        assert "path: 'tech'" in sidebar_content
        assert "label: '新文章'" in sidebar_content
        assert "to: '/blog/new-post'" in sidebar_content

        config_content = settings.docusaurus_config_path.read_text(encoding="utf-8")
        assert "label: 'Tech'" in config_content
        assert "to: '/blog/tech'" in config_content

        entities = RegistryIndexService().list_entities(entity_type="article", q="新文章")
        assert entities.total == 1
        assert entities.items[0].entity_key == "blog:tech/new-post.md"
    finally:
        _restore_settings(original)


def test_blog_article_workflow_creates_missing_category_and_rebuilds_indexes(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        settings.docusaurus_config_path.write_text(_config_with_blog_dropdown(), encoding="utf-8")
        (settings.blog_dir / "authors.yml").write_text("lucan:\n  name: lucan\n", encoding="utf-8")
        settings.blog_sidebars_path.write_text(
            "const blogSidebars = [];\n\nexport default blogSidebars;\n",
            encoding="utf-8",
        )
        (settings.blog_dir / "index.md").write_text(
            "# 博客\n\n保留的首页介绍。\n\n## 分类目录\n",
            encoding="utf-8",
        )

        article = BlogArticleWorkflow().create_article(
            ArticleCreateDTO(
                type=ArticleType.blog,
                title="从零创建分类的文章",
                slug="workflow-new-category",
                description="workflow desc",
                body="Workflow body",
                category_path=["workflow"],
                authors=["lucan"],
                tags=["Workflow Tag"],
                date="2026-07-03T09:00:00+08:00",
            )
        )

        article_path = settings.blog_dir / "workflow" / "workflow-new-category.md"
        assert article.relative_path == "workflow/workflow-new-category.md"
        assert article_path.exists()
        article_content = article_path.read_text(encoding="utf-8")
        assert "title: 从零创建分类的文章" in article_content
        assert "slug: workflow-new-category" in article_content
        assert "Workflow body" in article_content

        categories_content = (settings.content_schema_dir / "categories.yml").read_text(encoding="utf-8")
        assert "type: blog" in categories_content
        assert "path:" in categories_content
        assert "- workflow" in categories_content
        assert "label: Workflow" in categories_content

        tags_content = (settings.content_schema_dir / "tags.yml").read_text(encoding="utf-8")
        assert "slug: workflow-tag" in tags_content
        assert "label: Workflow Tag" in tags_content

        index_content = (settings.blog_dir / "index.md").read_text(encoding="utf-8")
        assert index_content.startswith("# 博客\n\n保留的首页介绍。")
        assert "### [Workflow](/blog/workflow)" in index_content
        assert "- [从零创建分类的文章](/blog/workflow-new-category)" in index_content

        sidebar_content = settings.blog_sidebars_path.read_text(encoding="utf-8")
        assert "path: 'workflow'" in sidebar_content
        assert "label: '从零创建分类的文章'" in sidebar_content
        assert "to: '/blog/workflow-new-category'" in sidebar_content

        config_content = settings.docusaurus_config_path.read_text(encoding="utf-8")
        assert "label: 'Workflow'" in config_content
        assert "to: '/blog/workflow'" in config_content

        registry = RegistryIndexService()
        article_entities = registry.list_entities(entity_type="article", q="从零创建分类的文章")
        assert article_entities.total == 1
        assert article_entities.items[0].entity_key == "blog:workflow/workflow-new-category.md"
        assert article_entities.items[0].metadata["relative_path"] == "workflow/workflow-new-category.md"
        assert article_entities.items[0].metadata["tags"] == ["Workflow Tag"]
        assert article_entities.items[0].metadata["category_paths"] == ["blog:workflow"]

        with sqlite3.connect(settings.registry_index_path) as conn:
            category_rows = conn.execute(
                """
                SELECT category_path, is_primary, sort_order
                FROM article_categories
                WHERE article_entity_id = ?
                ORDER BY sort_order ASC
                """,
                (article_entities.items[0].id,),
            ).fetchall()
        assert category_rows == [("blog:workflow", 1, 0)]

        category_entities = registry.list_entities(entity_type="category", q="workflow")
        assert category_entities.total == 1
        assert category_entities.items[0].entity_key == "blog:workflow"

        tag_entities = registry.list_entities(entity_type="tag", q="Workflow Tag")
        assert tag_entities.total == 1
        assert tag_entities.items[0].entity_key == "workflow-tag"

        stats = registry.stats()
        assert stats.article_count == 1
        assert stats.category_count == 1
        assert stats.tag_count == 1
        assert stats.last_sync is not None
        assert stats.last_sync["sync_type"] == "article_create"
        assert stats.last_sync["status"] == "success"
    finally:
        _restore_settings(original)


def test_blog_article_workflow_rolls_back_files_when_late_sync_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        config_before = _config_with_blog_dropdown()
        sidebar_before = "const blogSidebars = [];\n\nexport default blogSidebars;\n"
        index_before = "# 博客\n\n原始首页介绍。\n\n## 分类目录\n"
        settings.docusaurus_config_path.write_text(config_before, encoding="utf-8")
        (settings.blog_dir / "authors.yml").write_text("lucan:\n  name: lucan\n", encoding="utf-8")
        settings.blog_sidebars_path.write_text(sidebar_before, encoding="utf-8")
        (settings.blog_dir / "index.md").write_text(index_before, encoding="utf-8")

        workflow = BlogArticleWorkflow()

        def fail_rebuild(*, sync_type: str = "full") -> None:
            raise RuntimeError(f"forced registry failure: {sync_type}")

        monkeypatch.setattr(workflow.registry_index, "rebuild", fail_rebuild)

        with pytest.raises(RuntimeError, match="forced registry failure"):
            workflow.create_article(
                ArticleCreateDTO(
                    type=ArticleType.blog,
                    title="需要回滚的文章",
                    slug="rollback-post",
                    description="rollback desc",
                    body="Rollback body",
                    category_path=["rollback"],
                    authors=["lucan"],
                    tags=["Rollback Tag"],
                    date="2026-07-04T09:00:00+08:00",
                )
            )

        assert not (settings.blog_dir / "rollback" / "rollback-post.md").exists()
        assert not (settings.blog_dir / "rollback").exists()
        assert not (settings.content_schema_dir / "categories.yml").exists()
        assert not (settings.content_schema_dir / "tags.yml").exists()
        assert (settings.blog_dir / "index.md").read_text(encoding="utf-8") == index_before
        assert settings.blog_sidebars_path.read_text(encoding="utf-8") == sidebar_before
        assert settings.docusaurus_config_path.read_text(encoding="utf-8") == config_before
    finally:
        _restore_settings(original)


def test_blog_category_mutations_sync_nav_sidebar_and_index(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        settings.docusaurus_config_path.write_text(_config_with_blog_dropdown(), encoding="utf-8")
        settings.blog_sidebars_path.write_text("const blogSidebars = [];\n\nexport default blogSidebars;\n", encoding="utf-8")
        (settings.blog_dir / "index.md").write_text("# 博客\n\n保留介绍。\n\n## 分类目录\n", encoding="utf-8")

        service = CategoryService()
        service.create_category(
            CategoryCreateDTO(
                type=ArticleType.blog,
                path=["随笔感想"],
                label="随笔感想",
                description="阶段观察",
            )
        )

        config = settings.docusaurus_config_path.read_text(encoding="utf-8")
        sidebar = settings.blog_sidebars_path.read_text(encoding="utf-8")
        index = (settings.blog_dir / "index.md").read_text(encoding="utf-8")
        assert "label: '随笔感想'" in config
        assert "to: '/blog/随笔感想'" in config
        assert "path: '随笔感想'" in sidebar
        assert "### [随笔感想](/blog/随笔感想)" in index
        assert "阶段观察" in index
        registry = RegistryIndexService()
        category_entities = registry.list_entities(entity_type="category", q="随笔感想")
        assert category_entities.total == 1
        assert registry.stats().last_sync["sync_type"] == "blog_category_create"

        category_id = CategoryIdService.encode(ArticleType.blog, ["随笔感想"])
        service.update_category(category_id, CategoryUpdateDTO(label="生活随笔", description="生活记录"))

        assert "label: '生活随笔'" in settings.docusaurus_config_path.read_text(encoding="utf-8")
        assert "label: '生活随笔'" in settings.blog_sidebars_path.read_text(encoding="utf-8")
        assert "### [生活随笔](/blog/随笔感想)" in (settings.blog_dir / "index.md").read_text(encoding="utf-8")
        assert "生活记录" in (settings.blog_dir / "index.md").read_text(encoding="utf-8")
        category_entities = registry.list_entities(entity_type="category", q="生活随笔")
        assert category_entities.total == 1
        assert registry.stats().last_sync["sync_type"] == "blog_category_update"

        service.rename_category(
            category_id,
            CategoryRenameDTO(
                target_slug="生活记录",
                target_label="生活记录",
                dry_run=False,
                confirm=True,
            ),
        )

        config = settings.docusaurus_config_path.read_text(encoding="utf-8")
        sidebar = settings.blog_sidebars_path.read_text(encoding="utf-8")
        index = (settings.blog_dir / "index.md").read_text(encoding="utf-8")
        assert "to: '/blog/生活记录'" in config
        assert "to: '/blog/随笔感想'" not in config
        assert "path: '生活记录'" in sidebar
        assert "path: '随笔感想'" not in sidebar
        assert "### [生活记录](/blog/生活记录)" in index
        assert "### [生活随笔](/blog/随笔感想)" not in index
        category_entities = registry.list_entities(entity_type="category", q="生活记录")
        assert category_entities.total == 1
        assert category_entities.items[0].entity_key == "blog:生活记录"
        assert registry.stats().last_sync["sync_type"] == "blog_category_rename"

        renamed_id = CategoryIdService.encode(ArticleType.blog, ["生活记录"])
        service.delete_category(renamed_id, dry_run=False, confirm=True)

        config = settings.docusaurus_config_path.read_text(encoding="utf-8")
        sidebar = settings.blog_sidebars_path.read_text(encoding="utf-8")
        index = (settings.blog_dir / "index.md").read_text(encoding="utf-8")
        assert "to: '/blog/生活记录'" not in config
        assert "path: '生活记录'" not in sidebar
        assert "### [生活记录](/blog/生活记录)" not in index
        assert not (settings.blog_dir / "生活记录").exists()
        category_entities = registry.list_entities(entity_type="category", q="生活记录")
        assert category_entities.total == 0
        assert registry.stats().last_sync["sync_type"] == "blog_category_delete"
    finally:
        _restore_settings(original)


def test_blog_article_delete_syncs_sidebar_and_index(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        settings.docusaurus_config_path.write_text(_config_with_blog_dropdown(), encoding="utf-8")
        _write_blog_article(settings.blog_dir / "随笔感想" / "旧标题.md", "旧标题")
        service = ArticleService()
        SidebarManagementService().sync(SidebarSyncDTO(type="blog", mode="sync_categories", dry_run=False, confirm=True))
        BlogIndexService().sync_all(dry_run=False, confirm=True)

        article_id = service.encode_article_id(ArticleType.blog, "随笔感想/旧标题.md")
        service.delete_article(article_id, dry_run=False, confirm=True)

        assert not (settings.blog_dir / "随笔感想" / "旧标题.md").exists()
        sidebar = settings.blog_sidebars_path.read_text(encoding="utf-8")
        index = (settings.blog_dir / "index.md").read_text(encoding="utf-8")
        assert "label: '旧标题'" not in sidebar
        assert "to: '/blog/旧标题'" not in sidebar
        assert "- [旧标题](/blog/旧标题)" not in index
        assert "- 暂无文章" in index
        registry = RegistryIndexService()
        assert registry.list_entities(entity_type="article", q="旧标题").total == 0
        assert registry.stats().last_sync["sync_type"] == "blog_article_change"
    finally:
        _restore_settings(original)


def test_blog_article_move_syncs_nav_sidebar_and_index(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        settings.docusaurus_config_path.write_text(_config_with_blog_dropdown(), encoding="utf-8")
        _write_blog_article(settings.blog_dir / "随笔感想" / "旧标题.md", "旧标题")
        service = ArticleService()

        article_id = service.encode_article_id(ArticleType.blog, "随笔感想/旧标题.md")
        service.move_article(
            article_id,
            ArticleMoveDTO(
                target_type=ArticleType.blog,
                target_slug="新标题",
                target_category_path=["新分类"],
                dry_run=False,
                confirm=True,
            ),
        )

        assert not (settings.blog_dir / "随笔感想" / "旧标题.md").exists()
        assert (settings.blog_dir / "新分类" / "新标题.md").exists()

        config = settings.docusaurus_config_path.read_text(encoding="utf-8")
        sidebar = settings.blog_sidebars_path.read_text(encoding="utf-8")
        index = (settings.blog_dir / "index.md").read_text(encoding="utf-8")
        assert "to: '/blog/新分类'" in config
        assert "path: '新分类'" in sidebar
        assert "to: '/blog/新标题'" in sidebar
        assert "- [旧标题](/blog/新标题)" in index
        registry = RegistryIndexService()
        article_entities = registry.list_entities(entity_type="article", q="旧标题")
        assert article_entities.total == 1
        assert article_entities.items[0].entity_key == "blog:新分类/新标题.md"
        assert registry.stats().last_sync["sync_type"] == "blog_article_change"
    finally:
        _restore_settings(original)
