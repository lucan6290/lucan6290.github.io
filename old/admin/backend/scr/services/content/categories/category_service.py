"""分类注册表服务。"""

from scr.core.config import settings
from scr.models.article import ArticleType
from scr.schemas.category import CategoryCreateDTO, CategoryDTO, CategoryRenameDTO, CategoryUpdateDTO
from scr.schemas.common import MutationPlanDTO
from scr.services.content.categories.category_create_service import CategoryCreateService
from scr.services.content.categories.category_delete_service import CategoryDeleteService
from scr.services.content.categories.category_directory_service import CategoryDirectoryService
from scr.services.content.categories.category_query_service import CategoryQueryService
from scr.services.content.categories.category_registry_entry_service import CategoryRegistryEntryService
from scr.services.content.categories.category_rename_service import CategoryRenameService
from scr.services.content.categories.category_registry_service import CategoryRegistryService
from scr.services.content.categories.category_update_service import CategoryUpdateService


class CategoryService:
    """维护内容分类树，兼容 schema 注册表与 docs 目录推导。"""

    def __init__(self) -> None:
        self.registry = CategoryRegistryService()
        self.registry_entries = CategoryRegistryEntryService()
        self.directories = CategoryDirectoryService()
        self.query = CategoryQueryService()
        self.category_create = CategoryCreateService()
        self.category_update = CategoryUpdateService()
        self.category_rename = CategoryRenameService()
        self.category_delete = CategoryDeleteService()

    def type_label(self, article_type: ArticleType) -> str:
        """返回内容类型显示名。"""
        return self.query.type_label(article_type)

    def resolve_article_category(
        self,
        article_type: ArticleType,
        category_path: list[str],
        candidates: list[str] | None = None,
    ) -> tuple[list[str], str]:
        """根据文章路径、Front Matter 或标签解析分类路径与显示名。"""
        return self.query.resolve_article_category(article_type, category_path, candidates)

    def list_categories(
        self,
        *,
        article_type: ArticleType | None = None,
        include_empty: bool = True,
        include_counts: bool = False,
    ) -> list[CategoryDTO]:
        """返回分类树；schema 不存在时从 docs 目录推导。"""
        return self.query.list_categories(
            article_type=article_type,
            include_empty=include_empty,
            include_counts=include_counts,
        )

    def create_category(self, payload: CategoryCreateDTO) -> CategoryDTO:
        """创建分类；docs 一级分类会创建目录页并同步知识库顶部导航。"""
        return self.category_create.create_category(payload)

    def update_category(self, category_id: str, payload: CategoryUpdateDTO) -> CategoryDTO:
        """更新分类注册表中的展示信息；不会移动真实目录。"""
        return self.category_update.update_category(category_id, payload)

    def rename_category(self, category_id: str, payload: CategoryRenameDTO) -> MutationPlanDTO:
        """重命名分类路径，并同步 docs 目录、侧边栏、注册表和明确命中的站内链接。"""
        return self.category_rename.rename_category(category_id, payload)

    def delete_category(
        self,
        category_id: str,
        *,
        dry_run: bool = True,
        confirm: bool = False,
    ) -> MutationPlanDTO:
        """删除分类及其真实内容目录，并同步清理注册表和 docs 侧边栏登记。"""
        return self.category_delete.delete_category(category_id, dry_run=dry_run, confirm=confirm)

    def ensure_category_path(self, article_type: ArticleType, path: list[str]) -> list[str]:
        """确保分类路径存在于目录与注册表中，返回每级分类显示名。"""
        normalized_path = [segment.strip() for segment in path if segment.strip()]
        if not normalized_path:
            return []

        if article_type in {ArticleType.docs, ArticleType.blog}:
            target_dir = self.directories.category_dir(article_type, normalized_path)
            target_dir.mkdir(parents=True, exist_ok=True)

        entries = self.registry.load_entries()
        labels: list[str] = []
        changed = False
        for index in range(1, len(normalized_path) + 1):
            current_path = normalized_path[:index]
            entry = self.registry_entries.find_or_create_entry(entries, article_type, current_path)
            if "sort_order" not in entry or entry.get("sort_order") is None:
                entry["sort_order"] = self.registry_entries.next_sort_order(entries, article_type, index)
                changed = True
            if "enabled" not in entry:
                entry["enabled"] = True
                changed = True
            labels.append(str(entry.get("label") or current_path[-1]))
            if entry.get("label") is None:
                entry["label"] = current_path[-1]
                changed = True

        if changed:
            settings.content_schema_dir.mkdir(parents=True, exist_ok=True)
            self.registry.write_entries(entries)

        return labels

    def category_path_exists(self, article_type: ArticleType, path: list[str]) -> bool:
        """判断指定分类路径是否已存在。"""
        return self.query.category_path_exists(article_type, path)

    def snapshot_registry(self) -> str | None:
        """返回当前 categories.yml 原始内容，供调用方在失败时回滚；文件不存在时返回 None。"""
        return self.registry.snapshot()

    def restore_registry(self, snapshot: str | None) -> None:
        """用快照恢复 categories.yml。

        snapshot 为 None 表示快照时文件尚不存在，恢复时删除本次新建的注册表文件；
        否则用快照内容覆盖，撤销 ensure_category_path 写入的条目。
        """
        self.registry.restore(snapshot)
