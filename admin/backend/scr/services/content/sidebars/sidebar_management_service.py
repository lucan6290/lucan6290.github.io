"""侧边栏状态与同步服务。"""

from pathlib import Path

from scr.core.config import settings
from scr.core.exceptions import BadRequestError, NotFoundError
from scr.models.article import ArticleType
from scr.schemas.common import FileChangeDTO, MutationPlanDTO
from scr.schemas.sidebar import SidebarStatusDTO, SidebarSyncDTO
from scr.services.content.sidebars.blog_sidebar_service import BlogSidebarService
from scr.infrastructure.filesystem.filesystem_service import FileSystemService
from scr.services.content.sidebars.sidebar_service import SidebarService


class SidebarManagementService:
    """对账 docs/blog 侧边栏配置，并执行安全同步。"""

    def __init__(self) -> None:
        self.filesystem = FileSystemService()
        self.sidebar = SidebarService()
        self.blog_sidebar = BlogSidebarService()

    def get_status(self, *, include_details: bool = True, type: str = "docs") -> SidebarStatusDTO:
        """获取 docs 或 blog 侧边栏对账状态。"""
        if type == "blog":
            return self._get_blog_status(include_details=include_details)
        if type != "docs":
            raise BadRequestError(
                "不支持的侧边栏类型。",
                code="unsupported_sidebar_type",
                details={"type": type},
            )
        return self._get_docs_status(include_details=include_details)

    def _get_docs_status(self, *, include_details: bool = True) -> SidebarStatusDTO:
        """获取 sidebars.ts 与 docs 文件之间的差异。"""
        docs_ids = self._docs_doc_ids()
        registered_ids = self.sidebar.list_registered_doc_ids()
        missing = sorted(docs_ids - registered_ids)
        orphan = sorted(registered_ids - docs_ids)

        return SidebarStatusDTO(
            type="docs",
            sidebars_exists=settings.sidebars_path.exists(),
            sidebars_path=self._project_relative_posix_path(settings.sidebars_path),
            docs_count=len(docs_ids),
            registered_count=len(registered_ids),
            missing_count=len(missing),
            orphan_count=len(orphan),
            registered_doc_ids=sorted(registered_ids) if include_details else [],
            missing_in_sidebars=missing if include_details else [],
            orphan_sidebar_ids=orphan if include_details else [],
        )

    def _get_blog_status(self, *, include_details: bool = True) -> SidebarStatusDTO:
        """获取 blogSidebars.ts 与 blog 一级分类之间的差异。"""
        actual = self.blog_sidebar.actual_categories()
        registered = self.blog_sidebar.list_registered_categories()
        missing = self.blog_sidebar.missing_categories()
        orphan = self.blog_sidebar.orphan_categories()

        return SidebarStatusDTO(
            type="blog",
            sidebars_exists=settings.blog_sidebars_path.exists(),
            sidebars_path=self._project_relative_posix_path(settings.blog_sidebars_path),
            docs_count=0,
            registered_count=len(registered),
            missing_count=len(missing),
            orphan_count=len(orphan),
            registered_doc_ids=[],
            missing_in_sidebars=[item.path for item in missing] if include_details else [],
            orphan_sidebar_ids=[item.path for item in orphan] if include_details else [],
            blog_category_count=len(actual),
            registered_categories=[self.blog_sidebar.to_dto(item) for item in registered] if include_details else [],
            missing_blog_categories=[self.blog_sidebar.to_dto(item) for item in missing] if include_details else [],
            orphan_blog_sidebar_items=[self.blog_sidebar.to_dto(item) for item in orphan] if include_details else [],
        )

    def sync(self, payload: SidebarSyncDTO) -> MutationPlanDTO:
        """同步 docs 或 blog 侧边栏。"""
        if payload.type == "blog":
            return self._sync_blog(payload)
        if payload.type != "docs":
            raise BadRequestError(
                "不支持的侧边栏类型。",
                code="unsupported_sidebar_type",
                details={"type": payload.type},
            )
        return self._sync_docs(payload)

    def _sync_docs(self, payload: SidebarSyncDTO) -> MutationPlanDTO:
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

    def _sync_blog(self, payload: SidebarSyncDTO) -> MutationPlanDTO:
        """同步 blog 侧边栏分类项。"""
        if payload.mode != "sync_categories":
            raise BadRequestError(
                "blog 侧边栏当前仅支持 sync_categories 同步模式。",
                code="unsupported_sidebar_sync_mode",
                details={"mode": payload.mode},
            )

        status = self._get_blog_status(include_details=True)
        target = self._project_relative_posix_path(settings.blog_sidebars_path)
        changes: list[FileChangeDTO] = []

        if not settings.blog_sidebars_path.exists():
            changes.append(
                FileChangeDTO(
                    action="create",
                    target=target,
                    description="创建 blogSidebars.ts" if payload.dry_run else "已创建 blogSidebars.ts",
                )
            )
        for item in status.missing_blog_categories:
            changes.append(
                FileChangeDTO(
                    action="update",
                    target=target,
                    description=(
                        f"追加 blog 一级分类「{item.label}」（to: {item.to}）"
                        if payload.dry_run
                        else f"已追加 blog 一级分类「{item.label}」"
                    ),
                )
            )
        for item in status.orphan_blog_sidebar_items:
            changes.append(
                FileChangeDTO(
                    action="delete",
                    target=target,
                    description=(
                        f"移除不存在的 blog 侧边栏分类「{item.label}」（path: {item.path}）"
                        if payload.dry_run
                        else f"已移除不存在的 blog 侧边栏分类「{item.label}」"
                    ),
                )
            )

        if payload.dry_run:
            return MutationPlanDTO(dry_run=True, requires_confirmation=True, changes=changes, warnings=[])
        if not payload.confirm:
            raise BadRequestError("同步 blog 侧边栏需要显式确认。", code="confirmation_required")

        self.blog_sidebar.write_categories(self.blog_sidebar.synced_categories())
        return MutationPlanDTO(dry_run=False, requires_confirmation=False, changes=changes, warnings=[])

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
