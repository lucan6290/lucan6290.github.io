from pathlib import Path

from scr.core.config import settings
from scr.infrastructure.registry.tag_registry_service import TagRegistryService
from scr.infrastructure.registry.tag_slug_service import TagSlugService


def test_tag_slug_service_keeps_existing_normalization_behavior() -> None:
    service = TagSlugService()

    assert service.slug_from_label("AI Tools") == "ai-tools"
    assert service.slug_from_label("hello_world") == "hello-world"
    assert service.slug_from_label("C++ Tips") == "c-tips"
    assert service.slug_from_label("人工智能") == "tag-63fe855a00"


def test_tag_registry_service_reads_legacy_list_and_writes_normalized_mapping(tmp_path: Path) -> None:
    original_project_root = settings.project_root
    original_schema_dir = settings.content_schema_dir
    try:
        schema_dir = tmp_path / "admin" / "backend" / "data" / "content-schema"
        schema_dir.mkdir(parents=True)
        object.__setattr__(settings, "project_root", tmp_path)
        object.__setattr__(settings, "content_schema_dir", schema_dir)

        registry_path = schema_dir / "tags.yml"
        registry_path.write_text(
            "- slug: ai\n"
            "  label: AI\n"
            "  description: model notes\n",
            encoding="utf-8",
        )

        service = TagRegistryService()
        entries = service.load_entries()

        assert entries == [{"slug": "ai", "label": "AI", "description": "model notes"}]

        service.write_entries([*entries, {"slug": "docusaurus", "label": "Docusaurus"}])

        content = registry_path.read_text(encoding="utf-8")
        assert content.startswith("tags:\n")
        assert "slug: ai" in content
        assert "slug: docusaurus" in content
    finally:
        object.__setattr__(settings, "project_root", original_project_root)
        object.__setattr__(settings, "content_schema_dir", original_schema_dir)
