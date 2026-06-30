"""内容 Schema 汇总与初始化服务。"""

from pathlib import Path
from typing import Any

import yaml

from scr.core.config import settings
from scr.core.exceptions import AppError, BadRequestError, ConflictError
from scr.schemas.common import FileChangeDTO, MutationPlanDTO
from scr.schemas.schema import ContentSchemaDTO, SchemaInitDTO, SchemaInitResultDTO
from scr.services.content.category_service import CategoryService
from scr.services.content.tag_service import TagService


class SchemaService:
    """读取与初始化 admin/backend/data/content-schema 目录下的内容规则文件。"""

    def __init__(self) -> None:
        self.category_service = CategoryService()
        self.tag_service = TagService()
        self.frontmatter_path = settings.content_schema_dir / "frontmatter.yml"

    def get_schema(self) -> ContentSchemaDTO:
        """返回分类、标签、Front Matter 规则和模板摘要汇总。"""
        try:
            frontmatter = self._read_mapping_file(
                self.frontmatter_path,
                default={},
                invalid_code="frontmatter_schema_invalid",
                invalid_message="Front Matter schema 格式错误。",
            )
            return ContentSchemaDTO(
                categories=self.category_service.list_categories(include_counts=True),
                tags=self.tag_service.list_tags(page=1, page_size=200, sort="label"),
                frontmatter=frontmatter,
            )
        except BadRequestError:
            raise
        except OSError as exc:
            raise AppError("读取内容 Schema 失败。", code="schema_read_failed") from exc

    def init_schema(self, payload: SchemaInitDTO) -> MutationPlanDTO | SchemaInitResultDTO:
        """初始化 admin/backend/data/content-schema 目录下的基础 schema 文件。"""
        targets = self._default_files()
        existing = [path for path in targets if path.exists()]
        changes = self._build_changes(targets, payload.overwrite)
        warnings = self._build_warnings(existing, payload.overwrite)

        if payload.dry_run:
            return MutationPlanDTO(
                dry_run=True,
                requires_confirmation=True,
                changes=changes,
                warnings=warnings,
            )

        if not payload.confirm:
            raise BadRequestError("初始化内容 Schema 需要显式确认。", code="confirmation_required")
        if existing and len(existing) == len(targets) and not payload.overwrite:
            raise ConflictError(
                "Schema 文件已存在。",
                code="schema_already_exists",
                details={"files": [self._project_relative_posix_path(path) for path in existing]},
            )

        try:
            settings.content_schema_dir.mkdir(parents=True, exist_ok=True)
            created: list[str] = []
            overwritten: list[str] = []
            skipped: list[str] = []

            for path, data in targets.items():
                relative_path = self._project_relative_posix_path(path)
                if path.exists() and not payload.overwrite:
                    skipped.append(relative_path)
                    continue

                content = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
                path.write_text(content, encoding="utf-8")
                if path in existing:
                    overwritten.append(relative_path)
                else:
                    created.append(relative_path)

            return SchemaInitResultDTO(
                created=created,
                overwritten=overwritten,
                skipped=skipped,
                warnings=warnings,
            )
        except OSError as exc:
            raise AppError("初始化内容 Schema 失败。", code="schema_init_failed") from exc

    def _build_changes(self, targets: dict[Path, dict[str, Any]], overwrite: bool) -> list[FileChangeDTO]:
        changes: list[FileChangeDTO] = []
        for path in targets:
            exists = path.exists()
            if exists and not overwrite:
                continue
            relative_path = self._project_relative_posix_path(path)
            changes.append(
                FileChangeDTO(
                    action="update" if exists else "create",
                    target=relative_path,
                    description=self._description_for(path, exists, overwrite),
                )
            )
        return changes

    def _build_warnings(self, existing: list[Path], overwrite: bool) -> list[str]:
        if not existing:
            return []
        files = "、".join(self._project_relative_posix_path(path) for path in existing)
        if overwrite:
            return [f"以下 schema 文件将被覆盖：{files}。"]
        return [f"以下 schema 文件已存在，执行时会跳过：{files}。"]

    def _read_mapping_file(
        self,
        path: Path,
        *,
        default: dict[str, Any],
        invalid_code: str,
        invalid_message: str,
    ) -> dict[str, Any]:
        if not path.exists():
            return dict(default)
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise BadRequestError(invalid_message, code=invalid_code) from exc
        if not isinstance(loaded, dict):
            raise BadRequestError(invalid_message, code=invalid_code)
        return loaded

    def _default_files(self) -> dict[Path, dict[str, Any]]:
        return {
            settings.content_schema_dir / "categories.yml": {"categories": []},
            settings.content_schema_dir / "tags.yml": {"tags": []},
            self.frontmatter_path: self._default_frontmatter_schema(),
        }

    @staticmethod
    def _default_frontmatter_schema() -> dict[str, Any]:
        return {
            "frontmatter": {
                "docs": {
                    "required": ["title", "description"],
                    "optional": ["sidebar_position", "tags", "keywords", "draft"],
                },
                "blog": {
                    "required": ["title", "date", "authors"],
                    "optional": ["description", "tags", "keywords", "slug", "draft"],
                },
            }
        }

    @staticmethod
    def _description_for(path: Path, exists: bool, overwrite: bool) -> str:
        verb = "覆盖" if exists and overwrite else "初始化"
        name = path.name
        descriptions = {
            "categories.yml": f"{verb}分类 schema",
            "tags.yml": f"{verb}标签 schema",
            "frontmatter.yml": f"{verb} Front Matter schema",
        }
        return descriptions.get(name, f"{verb}内容 schema")

    @staticmethod
    def _project_relative_posix_path(path: Path) -> str:
        try:
            return path.resolve().relative_to(settings.project_root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()
