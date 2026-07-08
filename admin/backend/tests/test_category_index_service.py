"""docs 一级分类目录页维护回归测试。"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from scr.core.config import settings  # noqa: E402
from scr.services.content.categories.category_index_service import CategoryIndexService  # noqa: E402
from scr.services.content.sidebars.sidebar_service import SidebarService  # noqa: E402


BASE_SIDEBARS = """\
import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  'project-practiceSidebar': [
    {
      type: 'category',
      label: '项目实战',
      collapsed: false,
      items: [
        {
          type: 'category',
          label: '开发规范',
          collapsed: false,
          items: [
            'project-practice/development-standards/单人全栈开发高效流程',
          ],
        },
      ],
    },
  ],
};

export default sidebars;
"""


def _write_doc(path: Path, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\ntitle: {title}\n---\n\n# {title}\n", encoding="utf-8")


def test_category_index_and_sidebar_link() -> None:
    original_docs_dir = settings.docs_dir
    original_sidebars_path = settings.sidebars_path
    original_schema_dir = settings.content_schema_dir
    original_project_root = settings.project_root
    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs_dir = root / "site" / "docs"
            schema_dir = root / "admin" / "backend" / "data" / "content-schema"
            sidebars_path = root / "site" / "sidebars.ts"
            schema_dir.mkdir(parents=True)
            sidebars_path.parent.mkdir(parents=True)

            object.__setattr__(settings, "project_root", root)
            object.__setattr__(settings, "docs_dir", docs_dir)
            object.__setattr__(settings, "content_schema_dir", schema_dir)
            object.__setattr__(settings, "sidebars_path", sidebars_path)

            sidebars_path.write_text(BASE_SIDEBARS, encoding="utf-8")
            (schema_dir / "categories.yml").write_text(
                """\
categories:
- type: docs
  path: [project-practice]
  label: 项目实战
- type: docs
  path: [project-practice, development-standards]
  label: 开发规范
""",
                encoding="utf-8",
            )
            _write_doc(
                docs_dir / "project-practice" / "development-standards" / "单人全栈开发高效流程.md",
                "单人全栈开发高效流程",
            )
            _write_doc(
                docs_dir / "project-practice" / "development-standards" / "接口设计规范.md",
                "接口设计规范",
            )

            change = CategoryIndexService().sync_top_category("project-practice", force=True)
            SidebarService().ensure_category_doc_link("项目实战", "project-practice/index")

            index_content = (docs_dir / "project-practice" / "index.md").read_text(encoding="utf-8")
            sidebars_content = sidebars_path.read_text(encoding="utf-8")

            assert change is not None
            assert "## 当前内容" in index_content
            assert "## 开发规范" in index_content
            assert "- [单人全栈开发高效流程](./development-standards/单人全栈开发高效流程.md)" in index_content
            assert "- [接口设计规范](./development-standards/接口设计规范.md)" in index_content
            assert "link: {" in sidebars_content
            assert "id: 'project-practice/index'" in sidebars_content
            assert sidebars_content.count("'project-practice/index'") == 1
    finally:
        object.__setattr__(settings, "docs_dir", original_docs_dir)
        object.__setattr__(settings, "sidebars_path", original_sidebars_path)
        object.__setattr__(settings, "content_schema_dir", original_schema_dir)
        object.__setattr__(settings, "project_root", original_project_root)


def test_incremental_category_index_updates() -> None:
    original_docs_dir = settings.docs_dir
    original_schema_dir = settings.content_schema_dir
    original_project_root = settings.project_root
    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs_dir = root / "site" / "docs"
            schema_dir = root / "admin" / "backend" / "data" / "content-schema"
            schema_dir.mkdir(parents=True)

            object.__setattr__(settings, "project_root", root)
            object.__setattr__(settings, "docs_dir", docs_dir)
            object.__setattr__(settings, "content_schema_dir", schema_dir)

            (schema_dir / "categories.yml").write_text(
                """\
categories:
- type: docs
  path: [project-practice]
  label: 项目实战
- type: docs
  path: [project-practice, development-standards]
  label: 开发规范
""",
                encoding="utf-8",
            )

            svc = CategoryIndexService()
            svc.ensure_top_category_index("project-practice", "项目实战")
            svc.upsert_doc_link(
                "project-practice/development-standards/单人全栈开发高效流程.md",
                "单人全栈开发高效流程",
                ["项目实战", "开发规范"],
            )
            svc.upsert_doc_link(
                "project-practice/development-standards/接口设计规范.md",
                "接口设计规范",
                ["项目实战", "开发规范"],
            )
            svc.upsert_doc_link(
                "project-practice/development-standards/接口设计规范.md",
                "接口设计规范（更新版）",
                ["项目实战", "开发规范"],
            )
            svc.remove_doc_link("project-practice/development-standards/单人全栈开发高效流程.md")

            index_content = (docs_dir / "project-practice" / "index.md").read_text(encoding="utf-8")
            assert "## 开发规范" in index_content
            assert "单人全栈开发高效流程" not in index_content
            assert "- [接口设计规范（更新版）](./development-standards/接口设计规范.md)" in index_content
            assert index_content.count("./development-standards/接口设计规范.md") == 1
    finally:
        object.__setattr__(settings, "docs_dir", original_docs_dir)
        object.__setattr__(settings, "content_schema_dir", original_schema_dir)
        object.__setattr__(settings, "project_root", original_project_root)


if __name__ == "__main__":
    test_category_index_and_sidebar_link()
    test_incremental_category_index_updates()
    print("[PASS] category index service")
