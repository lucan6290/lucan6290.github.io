from pathlib import Path

import yaml

from scr.core.config import settings
from scr.models.article import ArticleType
from scr.schemas.category import CategoryCreateDTO, CategoryRenameDTO
from scr.services.content.categories.category_id_service import CategoryIdService
from scr.services.content.categories.category_service import CategoryService


def _set_temp_content_root(tmp_path: Path) -> dict[str, Path]:
    project_root = tmp_path
    site_dir = project_root / "site"
    content_schema_dir = project_root / "admin" / "backend" / "data" / "content-schema"
    paths = {
        "project_root": project_root,
        "site_dir": site_dir,
        "docs_dir": site_dir / "docs",
        "blog_dir": site_dir / "blog",
        "sidebars_path": site_dir / "sidebars.ts",
        "docusaurus_config_path": site_dir / "docusaurus.config.ts",
        "content_schema_dir": content_schema_dir,
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


def test_create_docs_top_category_creates_index_and_nav_item(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        settings.docusaurus_config_path.write_text(_knowledge_config(), encoding="utf-8")
        settings.sidebars_path.write_text(_empty_sidebars(), encoding="utf-8")

        service = CategoryService()
        category = service.create_category(
            CategoryCreateDTO(
                type=ArticleType.docs,
                path=["project-practice"],
                label="项目实战",
                description="项目实战分类目录页。",
            )
        )

        assert category.path == ["project-practice"]
        index_path = settings.docs_dir / "project-practice" / "index.md"
        assert index_path.exists()
        assert "title: 项目实战" in index_path.read_text(encoding="utf-8")
        config = settings.docusaurus_config_path.read_text(encoding="utf-8")
        assert "label: '项目实战'" in config
        assert "to: '/docs/project-practice'" in config
        sidebars = settings.sidebars_path.read_text(encoding="utf-8")
        assert "'project-practiceSidebar': [" in sidebars
        assert "label: '项目实战'" in sidebars
        assert "id: 'project-practice/index'" in sidebars
    finally:
        _restore_settings(original)


def test_create_docs_second_category_does_not_touch_nav(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        settings.docusaurus_config_path.write_text(_knowledge_config(), encoding="utf-8")
        settings.sidebars_path.write_text(_empty_sidebars(), encoding="utf-8")
        service = CategoryService()
        service.create_category(CategoryCreateDTO(type=ArticleType.docs, path=["tech-study"], label="技术研习"))
        before = settings.docusaurus_config_path.read_text(encoding="utf-8")

        service.create_category(
            CategoryCreateDTO(type=ArticleType.docs, path=["tech-study", "java-interview"], label="Java 面试题")
        )

        assert (settings.docs_dir / "tech-study" / "java-interview").is_dir()
        assert settings.docusaurus_config_path.read_text(encoding="utf-8") == before
        sidebars = settings.sidebars_path.read_text(encoding="utf-8")
        assert "'tech-studySidebar': [" in sidebars
        assert "label: '技术研习'" in sidebars
        assert "label: 'Java 面试题'" in sidebars
    finally:
        _restore_settings(original)


def test_delete_docs_category_syncs_directory_sidebars_and_registry(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        settings.sidebars_path.write_text(
            """const sidebars = {
  'tech-studySidebar': [
    {
      type: 'category',
      label: '技术研习',
      collapsed: false,
      link: {
        type: 'doc',
        id: 'tech-study/index',
      },
      items: [
        {
          type: 'category',
          label: 'Java 面试题',
          collapsed: false,
          items: [
            {
              type: 'category',
              label: 'Java 基础',
              collapsed: false,
              items: [
                'tech-study/java-interview/java-basic/java-vs-cpp',
              ],
            },
          ],
        },
        'tech-study/keep',
      ],
    },
  ],
};
export default sidebars;
""",
            encoding="utf-8",
        )
        settings.docusaurus_config_path.write_text(
            "export default { themeConfig: { navbar: { items: [{ to: '/docs/tech-study/java-interview' }] } } };",
            encoding="utf-8",
        )
        registry_path = settings.content_schema_dir / "categories.yml"
        registry_path.write_text(
            yaml.safe_dump(
                {
                    "categories": [
                        {"type": "docs", "path": ["tech-study"], "slug": "tech-study", "label": "技术研习"},
                        {
                            "type": "docs",
                            "path": ["tech-study", "java-interview"],
                            "slug": "java-interview",
                            "label": "Java 面试题",
                        },
                        {
                            "type": "docs",
                            "path": ["tech-study", "java-interview", "java-basic"],
                            "slug": "java-basic",
                            "label": "Java 基础",
                        },
                        {"type": "docs", "path": ["tech-study", "keep"], "slug": "keep", "label": "保留"},
                    ]
                },
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        article = settings.docs_dir / "tech-study" / "java-interview" / "java-basic" / "java-vs-cpp.md"
        article.parent.mkdir(parents=True, exist_ok=True)
        article.write_text("---\ntitle: Java vs C++\n---\n\nBody\n", encoding="utf-8")
        image_dir = article.with_name("java-vs-cpp-imgs")
        image_dir.mkdir()
        (image_dir / "cover.png").write_bytes(b"image")

        keep_article = settings.docs_dir / "tech-study" / "keep.md"
        keep_article.write_text("See /docs/tech-study/java-interview/java-basic/java-vs-cpp", encoding="utf-8")
        top_index = settings.docs_dir / "tech-study" / "index.md"
        top_index.write_text(
            "---\ntitle: 技术研习\ndescription: 技术研习分类目录页。\nsidebar_position: 1\n---\n\n"
            "# 技术研习\n\n## 当前内容\n\n"
            "## Java 面试题\n\n"
            "- [Java vs C++](./java-interview/java-basic/java-vs-cpp.md)\n\n"
            "## 保留\n\n"
            "- [保留](./keep.md)\n",
            encoding="utf-8",
        )

        service = CategoryService()
        category_id = CategoryIdService.encode(ArticleType.docs, ["tech-study", "java-interview"])

        plan = service.delete_category(category_id, dry_run=True)
        assert plan.dry_run is True
        assert any(change.action == "delete" for change in plan.changes)
        assert any(change.target.endswith("site/docs/tech-study/index.md") for change in plan.changes)
        assert any("旧链接" in warning for warning in plan.warnings)
        assert not any("docusaurus.config.ts" in warning for warning in plan.warnings)

        service.delete_category(category_id, dry_run=False, confirm=True)

        assert not (settings.docs_dir / "tech-study" / "java-interview").exists()
        assert keep_article.exists()
        sidebars = settings.sidebars_path.read_text(encoding="utf-8")
        assert "tech-study/java-interview/java-basic/java-vs-cpp" not in sidebars
        assert "label: 'Java 面试题'" not in sidebars
        assert "tech-study/keep" in sidebars
        top_index_content = top_index.read_text(encoding="utf-8")
        assert "Java 面试题" not in top_index_content
        assert "java-interview/java-basic/java-vs-cpp" not in top_index_content

        categories = yaml.safe_load(registry_path.read_text(encoding="utf-8"))["categories"]
        paths = [item["path"] for item in categories]
        assert ["tech-study", "java-interview"] not in paths
        assert ["tech-study", "java-interview", "java-basic"] not in paths
        assert ["tech-study"] in paths
        assert ["tech-study", "keep"] in paths
    finally:
        _restore_settings(original)


def test_delete_docs_top_category_removes_nav_item(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        settings.docusaurus_config_path.write_text(_knowledge_config(), encoding="utf-8")
        settings.sidebars_path.write_text(_empty_sidebars(), encoding="utf-8")
        service = CategoryService()
        service.create_category(CategoryCreateDTO(type=ArticleType.docs, path=["tech-study"], label="技术研习"))
        category_id = CategoryIdService.encode(ArticleType.docs, ["tech-study"])

        plan = service.delete_category(category_id, dry_run=True)
        assert any(change.target.endswith("site/docusaurus.config.ts") for change in plan.changes)

        service.delete_category(category_id, dry_run=False, confirm=True)

        assert not (settings.docs_dir / "tech-study").exists()
        config = settings.docusaurus_config_path.read_text(encoding="utf-8")
        assert "label: '技术研习'" not in config
        assert "to: '/docs/tech-study'" not in config
        sidebars = settings.sidebars_path.read_text(encoding="utf-8")
        assert "'tech-studySidebar': [" not in sidebars
        assert "label: '技术研习'" not in sidebars
    finally:
        _restore_settings(original)


def test_rename_docs_category_syncs_directory_sidebars_registry_links_and_nav(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        settings.sidebars_path.write_text(
            """const sidebars = {
  'tech-studySidebar': [
    {
      type: 'category',
      label: '技术研习',
      collapsed: false,
      link: {
        type: 'doc',
        id: 'tech-study/index',
      },
      items: [
        {
          type: 'category',
          label: 'Java 面试题',
          collapsed: false,
          items: [
            {
              type: 'category',
              label: 'Java 基础',
              collapsed: false,
              items: [
                'tech-study/java-interview/java-basic/java-vs-cpp',
              ],
            },
          ],
        },
        'tech-study/keep',
      ],
    },
  ],
};
export default sidebars;
""",
            encoding="utf-8",
        )
        settings.docusaurus_config_path.write_text(
            "export default { themeConfig: { navbar: { items: [{ to: '/docs/tech-study/java-interview' }] } } };",
            encoding="utf-8",
        )
        registry_path = settings.content_schema_dir / "categories.yml"
        registry_path.write_text(
            yaml.safe_dump(
                {
                    "categories": [
                        {"type": "docs", "path": ["tech-study"], "slug": "tech-study", "label": "技术研习"},
                        {
                            "type": "docs",
                            "path": ["tech-study", "java-interview"],
                            "slug": "java-interview",
                            "label": "Java 面试题",
                        },
                        {
                            "type": "docs",
                            "path": ["tech-study", "java-interview", "java-basic"],
                            "slug": "java-basic",
                            "label": "Java 基础",
                        },
                    ]
                },
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        article = settings.docs_dir / "tech-study" / "java-interview" / "java-basic" / "java-vs-cpp.md"
        article.parent.mkdir(parents=True, exist_ok=True)
        article.write_text("---\ntitle: Java vs C++\n---\n\nSee /docs/tech-study/java-interview\n", encoding="utf-8")

        keep_article = settings.docs_dir / "tech-study" / "keep.md"
        keep_article.write_text("See /docs/tech-study/java-interview/java-basic/java-vs-cpp", encoding="utf-8")

        service = CategoryService()
        category_id = CategoryIdService.encode(ArticleType.docs, ["tech-study", "java-interview"])

        plan = service.rename_category(
            category_id,
            CategoryRenameDTO(target_slug="java-guide", target_label="Java 指南"),
        )
        assert plan.dry_run is True
        assert any(change.action == "move" for change in plan.changes)
        assert any("sidebars.ts" in change.target for change in plan.changes)
        assert not any("docusaurus.config.ts" in change.target for change in plan.changes)

        service.rename_category(
            category_id,
            CategoryRenameDTO(
                target_slug="java-guide",
                target_label="Java 指南",
                dry_run=False,
                confirm=True,
            ),
        )

        assert not (settings.docs_dir / "tech-study" / "java-interview").exists()
        renamed_article = settings.docs_dir / "tech-study" / "java-guide" / "java-basic" / "java-vs-cpp.md"
        assert renamed_article.exists()

        sidebars = settings.sidebars_path.read_text(encoding="utf-8")
        assert "tech-study/java-interview/java-basic/java-vs-cpp" not in sidebars
        assert "tech-study/java-guide/java-basic/java-vs-cpp" in sidebars
        assert "label: 'Java 指南'" in sidebars
        assert "label: 'Java 面试题'" not in sidebars
        assert "tech-study/keep" in sidebars

        categories = yaml.safe_load(registry_path.read_text(encoding="utf-8"))["categories"]
        paths = [item["path"] for item in categories]
        assert ["tech-study", "java-interview"] not in paths
        assert ["tech-study", "java-guide"] in paths
        assert ["tech-study", "java-guide", "java-basic"] in paths
        assert any(item["path"] == ["tech-study", "java-guide"] and item["label"] == "Java 指南" for item in categories)

        assert "/docs/tech-study/java-guide/java-basic/java-vs-cpp" in keep_article.read_text(encoding="utf-8")
        assert "/docs/tech-study/java-interview" in settings.docusaurus_config_path.read_text(encoding="utf-8")
    finally:
        _restore_settings(original)


def test_rename_docs_top_category_updates_nav_item(tmp_path: Path) -> None:
    original = _set_temp_content_root(tmp_path)
    try:
        settings.docusaurus_config_path.write_text(_knowledge_config(), encoding="utf-8")
        settings.sidebars_path.write_text(_empty_sidebars(), encoding="utf-8")
        service = CategoryService()
        service.create_category(CategoryCreateDTO(type=ArticleType.docs, path=["tech-study"], label="技术研习"))
        category_id = CategoryIdService.encode(ArticleType.docs, ["tech-study"])

        service.rename_category(
            category_id,
            CategoryRenameDTO(target_slug="tech-lab", target_label="技术实验室", dry_run=False, confirm=True),
        )

        config = settings.docusaurus_config_path.read_text(encoding="utf-8")
        assert "label: '技术实验室'" in config
        assert "to: '/docs/tech-lab'" in config
        assert "to: '/docs/tech-study'" not in config
        sidebars = settings.sidebars_path.read_text(encoding="utf-8")
        assert "'tech-labSidebar': [" in sidebars
        assert "'tech-studySidebar': [" not in sidebars
        assert "label: '技术实验室'" in sidebars
        assert "id: 'tech-lab/index'" in sidebars
    finally:
        _restore_settings(original)
