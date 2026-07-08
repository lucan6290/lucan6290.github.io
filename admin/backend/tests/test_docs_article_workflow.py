from pathlib import Path

import sqlite3
import pytest

from scr.core.config import settings
from scr.models.article import ArticleType
from scr.schemas.article import ArticleCreateDTO
from scr.schemas.category import CategoryCreateDTO
from scr.services.content.articles.article_service import ArticleService
from scr.services.content.categories.category_service import CategoryService
from scr.infrastructure.registry.registry_index_service import RegistryIndexService
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


def _knowledge_config() -> str:
    return """export default {
  themeConfig: {
    navbar: {
      items: [
        {
          type: 'dropdown',
          label: '知识库',
          position: 'left',
          items: [
            {
              label: '首页',
              to: '/docs/index',
            },
          ],
        },
      ],
    },
  },
};
"""


def _empty_sidebars() -> str:
    return "const sidebars = {\n};\nexport default sidebars;\n"


def test_docs_article_workflow_syncs_sidebar_index_and_registry(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        settings.docusaurus_config_path.write_text(_knowledge_config(), encoding="utf-8")
        settings.sidebars_path.write_text(_empty_sidebars(), encoding="utf-8")

        category_service = CategoryService()
        category_service.create_category(
            CategoryCreateDTO(
                type=ArticleType.docs,
                path=["tech-study"],
                label="技术研习",
                description="技术研习分类目录页。",
            )
        )
        category_service.create_category(
            CategoryCreateDTO(
                type=ArticleType.docs,
                path=["tech-study", "java-basic"],
                label="Java 基础",
                description="Java 基础知识。",
            )
        )

        article = ArticleWorkflowService(ArticleService()).create_article(
            ArticleCreateDTO(
                type=ArticleType.docs,
                title="Java 集合基础",
                slug="java-collections",
                description="Java 集合体系入门。",
                body="正文内容",
                category_path=["tech-study", "java-basic"],
                sidebar_position=2,
                authors=["lucan"],
                date="2026-07-02T10:00:00+08:00",
            )
        )

        article_path = settings.docs_dir / "tech-study" / "java-basic" / "java-collections.md"
        assert article.relative_path == "tech-study/java-basic/java-collections.md"
        assert article_path.exists()
        article_content = article_path.read_text(encoding="utf-8")
        assert "title: Java 集合基础" in article_content
        assert "sidebar_position: 2" in article_content
        assert "正文内容" in article_content

        sidebars = settings.sidebars_path.read_text(encoding="utf-8")
        assert "'tech-studySidebar': [" in sidebars
        assert "label: '技术研习'" in sidebars
        assert "label: 'Java 基础'" in sidebars
        assert "'tech-study/java-basic/java-collections'" in sidebars

        index_content = (settings.docs_dir / "tech-study" / "index.md").read_text(encoding="utf-8")
        assert index_content.startswith("---\ntitle: 技术研习")
        assert "## 当前内容" in index_content
        assert "## Java 基础" in index_content
        assert "- [Java 集合基础](./java-basic/java-collections.md)" in index_content
        root_index_content = (settings.docs_dir / "index.md").read_text(encoding="utf-8")
        assert "## 知识库目录" in root_index_content
        assert "## [技术研习](./tech-study/)" in root_index_content
        assert "### Java 基础" in root_index_content
        assert "- [Java 集合基础](./tech-study/java-basic/java-collections.md)" in root_index_content

        registry = RegistryIndexService()
        article_entities = registry.list_entities(entity_type="article", q="Java 集合基础")
        article_by_key = {item.entity_key: item for item in article_entities.items}
        assert "docs:tech-study/index.md" in article_by_key
        assert "docs:tech-study/java-basic/java-collections.md" in article_by_key

        created_article = article_by_key["docs:tech-study/java-basic/java-collections.md"]
        assert created_article.metadata["relative_path"] == "tech-study/java-basic/java-collections.md"
        assert created_article.metadata["category_paths"] == [
            "docs:tech-study",
            "docs:tech-study/java-basic",
        ]

        with sqlite3.connect(settings.registry_index_path) as conn:
            category_rows = conn.execute(
                """
                SELECT category_path, is_primary, sort_order
                FROM article_categories
                WHERE article_entity_id = ?
                ORDER BY sort_order ASC
                """,
                (created_article.id,),
            ).fetchall()
        assert category_rows == [
            ("docs:tech-study", 1, 0),
            ("docs:tech-study/java-basic", 0, 1),
        ]

        stats = registry.stats()
        assert stats.article_count == 3
        assert stats.category_count == 2
        assert stats.last_sync is not None
        assert stats.last_sync["sync_type"] == "article_create"
        assert stats.last_sync["status"] == "success"
    finally:
        _restore_settings(original)


def test_docs_article_workflow_rolls_back_file_sidebar_and_index_when_late_sync_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        settings.docusaurus_config_path.write_text(_knowledge_config(), encoding="utf-8")
        settings.sidebars_path.write_text(_empty_sidebars(), encoding="utf-8")

        category_service = CategoryService()
        category_service.create_category(
            CategoryCreateDTO(
                type=ArticleType.docs,
                path=["tech-study"],
                label="技术研习",
                description="技术研习分类目录页。",
            )
        )
        category_service.create_category(
            CategoryCreateDTO(
                type=ArticleType.docs,
                path=["tech-study", "java-basic"],
                label="Java 基础",
                description="Java 基础知识。",
            )
        )

        sidebars_before = settings.sidebars_path.read_text(encoding="utf-8")
        top_index_path = settings.docs_dir / "tech-study" / "index.md"
        top_index_before = top_index_path.read_text(encoding="utf-8")
        root_index_path = settings.docs_dir / "index.md"
        root_index_before = root_index_path.read_text(encoding="utf-8")
        registry_existed_before = settings.registry_index_path.exists()
        workflow = ArticleWorkflowService(ArticleService())

        def fail_rebuild(*, sync_type: str = "full") -> None:
            raise RuntimeError(f"forced registry failure: {sync_type}")

        monkeypatch.setattr(workflow.docs.registry_index, "rebuild", fail_rebuild)

        with pytest.raises(RuntimeError, match="forced registry failure"):
            workflow.create_article(
                ArticleCreateDTO(
                    type=ArticleType.docs,
                    title="需要回滚的文档",
                    slug="rollback-doc",
                    description="rollback desc",
                    body="Rollback body",
                    category_path=["tech-study", "java-basic"],
                    sidebar_position=3,
                    authors=["lucan"],
                    date="2026-07-04T10:00:00+08:00",
                )
            )

        assert not (settings.docs_dir / "tech-study" / "java-basic" / "rollback-doc.md").exists()
        assert settings.sidebars_path.read_text(encoding="utf-8") == sidebars_before
        assert top_index_path.read_text(encoding="utf-8") == top_index_before
        assert root_index_path.read_text(encoding="utf-8") == root_index_before
        assert settings.registry_index_path.exists() is registry_existed_before
    finally:
        _restore_settings(original)
