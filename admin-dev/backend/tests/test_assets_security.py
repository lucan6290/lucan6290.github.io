from __future__ import annotations

from pathlib import Path

import pytest

from blog_admin.core.errors import AppError, InvalidPathError
from blog_admin.modules.assets.repository import AssetRepository
from blog_admin.modules.assets.scanner import extract_referenced_image_names
from blog_admin.modules.assets.service import AssetService


def _make_assets(tmp_path: Path) -> tuple[AssetRepository, AssetService, Path]:
    blog_root = tmp_path / "blog-content"
    posts_dir = blog_root / "source" / "_posts"
    posts_dir.mkdir(parents=True)
    repository = AssetRepository(blog_root=blog_root, posts_dir=posts_dir)
    service = AssetService(blog_root=blog_root, posts_dir=posts_dir)
    return repository, service, posts_dir


def test_asset_repository_rejects_path_traversal(tmp_path: Path) -> None:
    repository, _, _ = _make_assets(tmp_path)

    with pytest.raises(InvalidPathError):
        repository.resolve_posts_path("../outside.png")


def test_asset_repository_rejects_absolute_path(tmp_path: Path) -> None:
    repository, _, _ = _make_assets(tmp_path)

    with pytest.raises(InvalidPathError):
        repository.resolve_posts_path(str(tmp_path / "outside.png"))


def test_asset_repository_rejects_non_image_preview(tmp_path: Path) -> None:
    repository, _, posts_dir = _make_assets(tmp_path)
    article_assets = posts_dir / "tech-study" / "ts-demo"
    article_assets.mkdir(parents=True)
    (article_assets / "note.txt").write_text("not image", encoding="utf-8")

    with pytest.raises(AppError) as exc_info:
        repository.get_asset_file("tech-study/ts-demo/note.txt")

    assert exc_info.value.code == "UNSUPPORTED_ASSET_PREVIEW"


def test_asset_repository_delete_missing_image_returns_unified_error(tmp_path: Path) -> None:
    repository, _, _ = _make_assets(tmp_path)

    with pytest.raises(AppError) as exc_info:
        repository.delete_image("tech-study/ts-demo/missing.png")

    assert exc_info.value.code == "ASSET_IMAGE_NOT_FOUND"
    assert exc_info.value.to_payload()["code"] == "ASSET_IMAGE_NOT_FOUND"


def test_extract_referenced_image_names_supports_markdown_html_and_hexo_asset_img() -> None:
    markdown = """
![markdown](img1.png)
![encoded](<folder/img%204.png?size=large#hash>)
<img src="img2.jpg" alt="html">
{% asset_img img3.webp 图片 %}
![external](https://example.com/outside.png)
<img src="/img/root.png">
<img src="data:image/png;base64,aaaa">
"""

    assert extract_referenced_image_names(markdown) == {"img1.png", "img 4.png", "img2.jpg", "img3.webp"}


def test_asset_service_unused_scan_uses_all_supported_reference_formats(tmp_path: Path) -> None:
    _, service, posts_dir = _make_assets(tmp_path)
    article_assets = posts_dir / "tech-study" / "ts-demo"
    article_assets.mkdir(parents=True)
    for name in ["img1.png", "img2.jpg", "img3.webp", "unused.gif"]:
        (article_assets / name).write_bytes(b"image")

    unused = service.list_unused_images(
        "tech-study/ts-demo.md",
        """
![markdown](img1.png)
<img src="img2.jpg">
{% asset_img img3.webp %}
""",
    )

    assert [item["name"] for item in unused] == ["unused.gif"]
