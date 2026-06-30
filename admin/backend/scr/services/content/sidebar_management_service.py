"""侧边栏状态与同步服务。"""

from pathlib import Path

from scr.core.config import settings
from scr.core.exceptions import BadRequestError, NotFoundError
from scr.models.article import ArticleType
from scr.schemas.common import FileChangeDTO, MutationPlanDTO
from scr.schemas.sidebar import SidebarStatusDTO, SidebarSyncDTO
from scr.services.content.filesystem_service import FileSystemService
from scr.services.content.sidebar_service import SidebarService


class SidebarManagementService:
    """对账 docs 文件与 sidebars.ts，并执行安全同步。"""

    def __init__(self) -> None:
        self.filesystem = FileSystemService()
        self.sidebar = SidebarService()

    def get_status(self, *, include_details: bool = True) -> SidebarStatusDTO:
        """获取 sidebars.ts 与 docs 文件之间的差异。"""
        docs_ids = self._docs_doc_ids()
        registered_ids = self.sidebar.list_registered_doc_ids()
        missing = sorted(docs_ids - registered_ids)
        orphan = sorted(registered_ids - docs_ids)

        return SidebarStatusDTO(
            sidebars_exists=settings.sidebars_path.exists(),
            docs_count=len(docs_ids),
            registered_count=len(registered_ids),
            missing_count=len(missing),
            orphan_count=len(orphan),
            registered_doc_ids=sorted(registered_ids) if include_details else [],
            missing_in_sidebars=missing if include_details else [],
            orphan_sidebar_ids=orphan if include_details else [],
        )

    def sync(self, payload: SidebarSyncDTO) -> MutationPlanDTO:
        """同步 docs 侧边栏；当前支持追加缺失 doc_id。"""
        if not settings.sidebars_path.exists():
            raise NotFoundError("site/sidebars.ts 不存在。", code="sidebars_missing")
        if payload.mode != "append_missing":
            raise BadRequestError(
                "当前仅支持 append_missing 同步模式。",
                code="unsupported_sidebar_sync_mode",
                details={"mode": payload.mode},
            )

        status = self.get_status(include_details=True)
        changes = [
            FileChangeDTO(
                action="update",
                target=self._project_relative_posix_path(settings.sidebars_path),
                description=(
                    f"追加 docs 文章 ID {doc_id}"
                    if payload.dry_run
                    else f"已追加 docs 文章 ID {doc_id}"
                ),
            )
            for doc_id in status.missing_in_sidebars
        ]
        warnings = []
        if status.orphan_sidebar_ids:
            warnings.append("sidebars.ts 中存在孤儿 docs ID，本接口不会自动删除。")

        plan = MutationPlanDTO(
            dry_run=payload.dry_run,
            requires_confirmation=payload.dry_run,
            changes=changes,
            warnings=warnings,
        )

        if payload.dry_run:
            return plan
        if not payload.confirm:
            raise BadRequestError("同步侧边栏需要显式确认。", code="confirmation_required")

        for doc_id in status.missing_in_sidebars:
            self.sidebar.append_doc_id(doc_id)

        return plan

    def _docs_doc_ids(self) -> set[str]:
        """返回当前 docs 文件推导出的全部 doc_id。"""
        doc_ids: set[str] = set()
        for path in self.filesystem.scan_article_files(ArticleType.docs):
            relative_path = self.filesystem.relative_posix_path(ArticleType.docs, path)
            doc_ids.add(self.sidebar.doc_id_from_relative_path(relative_path))
        return doc_ids

    @staticmethod
    def _project_relative_posix_path(path: Path) -> str:
        try:
            return path.resolve().relative_to(settings.project_root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()
