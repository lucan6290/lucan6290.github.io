from pathlib import Path

from scr.core.config import settings
from scr.schemas.registry_index import RegistryYamlEntriesSaveDTO
from scr.infrastructure.registry.registry_yaml_service import RegistryYamlService


def test_registry_yaml_entries_use_registry_services(tmp_path: Path) -> None:
    original_project_root = settings.project_root
    original_schema_dir = settings.content_schema_dir
    original_registry_index_path = settings.registry_index_path
    try:
        schema_dir = tmp_path / "admin" / "backend" / "data" / "content-schema"
        schema_dir.mkdir(parents=True)
        object.__setattr__(settings, "project_root", tmp_path)
        object.__setattr__(settings, "content_schema_dir", schema_dir)
        object.__setattr__(settings, "registry_index_path", tmp_path / "registry.sqlite3")

        tags_path = schema_dir / "tags.yml"
        tags_path.write_text("- slug: ai\n  label: AI\n", encoding="utf-8")

        service = RegistryYamlService()

        entries = service.get_yaml_entries("tags")
        assert entries.exists is True
        assert entries.items == [{"slug": "ai", "label": "AI"}]

        service.save_yaml_entries(
            "tags",
            RegistryYamlEntriesSaveDTO(
                items=[{"slug": "docusaurus", "label": "Docusaurus"}],
                rebuild_index=False,
            ),
            rebuild=lambda: None,
        )

        content = tags_path.read_text(encoding="utf-8")
        assert content.startswith("tags:\n")
        assert "slug: docusaurus" in content
    finally:
        object.__setattr__(settings, "project_root", original_project_root)
        object.__setattr__(settings, "content_schema_dir", original_schema_dir)
        object.__setattr__(settings, "registry_index_path", original_registry_index_path)
