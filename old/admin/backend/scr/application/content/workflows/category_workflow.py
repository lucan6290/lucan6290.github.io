"""Category workflow dispatcher."""

from scr.schemas.category import CategoryCreateDTO, CategoryDTO, CategoryRenameDTO, CategoryUpdateDTO
from scr.schemas.common import MutationPlanDTO
from scr.services.content.categories.category_service import CategoryService


class CategoryWorkflowService:
    """Coordinate user-facing category mutations.

    The first step keeps behavior delegated to CategoryService while giving API
    endpoints a stable workflow layer for future orchestration extraction.
    """

    def __init__(self, category_service: CategoryService | None = None) -> None:
        self.category_service = category_service or CategoryService()

    def create_category(self, payload: CategoryCreateDTO) -> CategoryDTO:
        return self.category_service.create_category(payload)

    def update_category(self, category_id: str, payload: CategoryUpdateDTO) -> CategoryDTO:
        return self.category_service.update_category(category_id, payload)

    def rename_category(self, category_id: str, payload: CategoryRenameDTO) -> MutationPlanDTO:
        return self.category_service.rename_category(category_id, payload)

    def delete_category(self, category_id: str, *, dry_run: bool = True, confirm: bool = False) -> MutationPlanDTO:
        return self.category_service.delete_category(category_id, dry_run=dry_run, confirm=confirm)
