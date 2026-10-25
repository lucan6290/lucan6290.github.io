"""SiteConfigSyncService 排序策略相关单元测试。

覆盖两个关键场景：
1. docs 侧边栏嵌套分类按 categories.yml 的 sort_order 排序，而非目录名字典序；
2. docs 侧边栏文章按现有 sidebars.ts 中 doc_id 的出现顺序保留。
"""

from pathlib import Path

import pytest

from scr.core.config import settings
from scr.models.article import ArticleType
from scr.services.content.sync.site_config_sync_service import SiteConfigSyncService
from scr.services.content.sync.site_content_scanner import SiteArticleSnapshot, SiteCategorySnapshot


def _category(path: tuple[str, ...], label: str, *, has_index: bool = False) -> SiteCategorySnapshot:
    return SiteCategorySnapshot(
        type=ArticleType.docs,
        path=path,
        label=label,
        has_index=has_index,
    )


def _article(doc_id: str, category_path: tuple[str, ...]) -> SiteArticleSnapshot:
    return SiteArticleSnapshot(
        type=ArticleType.docs,
        path=Path(f"{doc_id}.md"),
        relative_path=f"{doc_id}.md",
        doc_id=doc_id,
        title=doc_id.rsplit("/", 1)[-1],
        slug=doc_id.rsplit("/", 1)[-1],
        date="",
        category_path=category_path,
    )


def test_render_docs_sidebars_orders_nested_categories_by_sort_order() -> None:
    service = SiteConfigSyncService()
    categories = (
        _category(("tech",), "技术研习", has_index=True),
        _category(("tech", "B-cat"), "B Cat"),
        _category(("tech", "A-cat"), "A Cat"),
        _category(("tech", "C-cat"), "C Cat"),
    )
    sort_order_map = {
        ("docs", ("tech", "A-cat")): 30,
        ("docs", ("tech", "B-cat")): 10,
        ("docs", ("tech", "C-cat")): 20,
    }

    rendered = service._render_docs_sidebars(categories, (), sort_order_map, {})

    # 期望按 sort_order：B(10) -> C(20) -> A(30)，而不是目录名字典序 A/B/C。
    assert rendered.index("label: 'B Cat'") < rendered.index("label: 'C Cat'") < rendered.index("label: 'A Cat'")


def test_render_docs_sidebars_preserves_existing_article_order() -> None:
    service = SiteConfigSyncService()
    categories = (_category(("tech",), "技术研习"),)
    articles = (
        _article("tech/banana", ("tech",)),
        _article("tech/apple", ("tech",)),
        _article("tech/cherry", ("tech",)),
    )
    article_order = {
        "tech/banana": 0,
        "tech/apple": 1,
        "tech/cherry": 2,
    }

    rendered = service._render_docs_sidebars(categories, articles, {}, article_order)

    # 按 article_order 保留 banana -> apple -> cherry，而不是字典序 apple/banana/cherry。
    assert rendered.index("'tech/banana'") < rendered.index("'tech/apple'") < rendered.index("'tech/cherry'")


def test_render_docs_sidebars_appends_new_articles_after_existing() -> None:
    service = SiteConfigSyncService()
    categories = (_category(("tech",), "技术研习"),)
    articles = (
        _article("tech/banana", ("tech",)),
        _article("tech/new-one", ("tech",)),
        _article("tech/apple", ("tech",)),
    )
    article_order = {"tech/banana": 0, "tech/apple": 1}

    rendered = service._render_docs_sidebars(categories, articles, {}, article_order)

    # 已登记文章保留原顺序，新文章（不在 article_order）追加到末尾。
    assert rendered.index("'tech/banana'") < rendered.index("'tech/apple'") < rendered.index("'tech/new-one'")


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


def test_sort_order_and_article_order_helpers_read_from_files(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        (settings.content_schema_dir / "categories.yml").write_text(
            "categories:\n"
            "- type: docs\n"
            "  slug: tech-study\n"
            "  path:\n"
            "  - tech-study\n"
            "  label: 技术研习\n"
            "  sort_order: 10\n"
            "- type: docs\n"
            "  slug: project-practice\n"
            "  path:\n"
            "  - project-practice\n"
            "  label: 项目实战\n"
            "  sort_order: 30\n",
            encoding="utf-8",
        )
        settings.sidebars_path.write_text(
            "const sidebars = {\n"
            "  overviewSidebar: ['index'],\n"
            "  'tech-studySidebar': [\n"
            "    {\n"
            "      type: 'category',\n"
            "      label: '技术研习',\n"
            "      items: [\n"
            "        'tech-study/banana',\n"
            "        'tech-study/apple',\n"
            "      ],\n"
            "    },\n"
            "  ],\n"
            "};\n"
            "export default sidebars;\n",
            encoding="utf-8",
        )

        service = SiteConfigSyncService()

        assert service._registry_sort_orders() == {
            ("docs", ("tech-study",)): 10,
            ("docs", ("project-practice",)): 30,
        }

        article_order = service._existing_article_order()
        assert article_order["tech-study/banana"] < article_order["tech-study/apple"]
    finally:
        _restore_settings(original)
