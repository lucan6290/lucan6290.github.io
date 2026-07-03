"""分类端点。"""

from fastapi import APIRouter, Depends, Query

from scr.api.v1.dependencies import get_category_service, get_category_workflow_service
from scr.application.content.workflows.category_workflow import CategoryWorkflowService
from scr.models.article import ArticleType
from scr.schemas.category import CategoryCreateDTO, CategoryDTO, CategoryRenameDTO, CategoryUpdateDTO
from scr.schemas.common import MutationPlanDTO
from scr.services.content.categories.category_service import CategoryService


router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryDTO], response_model_exclude_none=True)
def list_categories(
    article_type: ArticleType | None = Query(default=None, alias="type"),
    include_empty: bool = Query(default=True),
    include_counts: bool = Query(default=False),
    category_service: CategoryService = Depends(get_category_service),
) -> list[CategoryDTO]:
    """获取分类树。"""
    return category_service.list_categories(
        article_type=article_type,
        include_empty=include_empty,
        include_counts=include_counts,
    )


@router.post("", response_model=CategoryDTO, response_model_exclude_none=True, status_code=201)
def create_category(
    payload: CategoryCreateDTO,
    category_workflow_service: CategoryWorkflowService = Depends(get_category_workflow_service),
) -> CategoryDTO:
    """创建一级或下级分类；docs 一级分类会同步知识库顶部导航。"""
    return category_workflow_service.create_category(payload)


@router.put("/{category_id}", response_model=CategoryDTO, response_model_exclude_none=True)
def update_category(
    category_id: str,
    payload: CategoryUpdateDTO,
    category_workflow_service: CategoryWorkflowService = Depends(get_category_workflow_service),
) -> CategoryDTO:
    """更新分类注册表中的展示信息。"""
    return category_workflow_service.update_category(category_id, payload)


@router.post(
    "/{category_id}/rename",
    response_model=MutationPlanDTO,
    response_model_exclude_none=True,
)
def rename_category(
    category_id: str,
    payload: CategoryRenameDTO,
    category_workflow_service: CategoryWorkflowService = Depends(get_category_workflow_service),
) -> MutationPlanDTO:
    """重命名分类路径；默认只返回影响分析，执行重命名需要显式确认。"""
    return category_workflow_service.rename_category(category_id, payload)


@router.delete(
    "/{category_id}",
    response_model=MutationPlanDTO,
    response_model_exclude_none=True,
)
def delete_category(
    category_id: str,
    dry_run: bool = Query(default=True),
    confirm: bool = Query(default=False),
    category_workflow_service: CategoryWorkflowService = Depends(get_category_workflow_service),
) -> MutationPlanDTO:
    """删除分类目录及其内容；默认只返回影响分析，执行删除需要显式确认。"""
    return category_workflow_service.delete_category(
        category_id,
        dry_run=dry_run,
        confirm=confirm,
    )
