from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from blog_admin.core.settings import settings
from blog_admin.modules.categories import registry as registry_module


def _write_blog_content(root: Path) -> None:
    posts_dir = root / "source" / "_posts"
    (root / "source" / "img" / "covers").mkdir(parents=True)
    posts_dir.mkdir(parents=True)
    (root / "config").mkdir(parents=True)
    (root / "_config.yml").write_text(
        """category_map:
  # ==========================================
  # 一级分类
  # ==========================================
  技术研习: tech-study

  # ==========================================
  # 技术研习 - 二级分类
  # ==========================================
  AI 探索: ai-exploration
tag_map:
""",
        encoding="utf-8",
    )
    (posts_dir / "index.md").write_text(
        """---
title: 博客文章目录
---

## 一、技术研习

*暂无文章，敬请期待*

---

*持续更新，记录成长*
""",
        encoding="utf-8",
    )


def test_save_category_registry_creates_primary_category_assets(tmp_path: Path, monkeypatch) -> None:
    blog_root = tmp_path / "blog-content"
    _write_blog_content(blog_root)
    next_settings = replace(
        settings,
        blog_root=blog_root,
        posts_dir=blog_root / "source" / "_posts",
        category_registry_path=blog_root / "config" / "category-registry.json",
    )
    monkeypatch.setattr(registry_module, "settings", next_settings)

    saved = registry_module.save_category_registry(
        [
            {
                "frontend_name1": "实验记录",
                "category_slug": "lab-notes",
                "note_prefix1": "lab",
                "sort_order": 60,
                "enabled": True,
                "children": [],
            }
        ]
    )

    assert saved[0]["cover"] == "/img/covers/lab-notes.svg"
    assert (blog_root / "source" / "_posts" / "lab-notes").is_dir()
    assert (blog_root / "source" / "img" / "covers" / "lab-notes.svg").is_file()
    assert "实验记录: lab-notes" in (blog_root / "_config.yml").read_text(encoding="utf-8")
    assert "## 二、实验记录" in (blog_root / "source" / "_posts" / "index.md").read_text(encoding="utf-8")


def test_validate_category_registry_rejects_unsafe_slug() -> None:
    errors = registry_module.validate_category_registry(
        [
            {
                "frontend_name1": "危险分类",
                "category_slug": "../outside",
                "note_prefix1": "bad",
                "children": [],
            }
        ]
    )

    assert any("category_slug 只能使用英文、数字、中划线或下划线" in error for error in errors)
