"""分类端点。"""

from fastapi import APIRouter, Query

from scr.models.article import ArticleType
from scr.schemas.category import CategoryDTO, CategoryUpdateDTO
from scr.services.content.category_service import CategoryService


router = APIRouter(prefix="/categories", tags=["categories"])
category_service = CategoryService()


@router.get("", response_model=list[CategoryDTO], response_model_exclude_none=True)
def list_categories(
    article_type: ArticleType | None = Query(default=None, alias="type"),
    include_empty: bool = Query(default=True),
    include_counts: bool = Query(default=False),
) -> list[CategoryDTO]:
    """获取分类树。"""
    return category_service.list_categories(
        article_type=article_type,
        include_empty=include_empty,
        include_counts=include_counts,
    )


@router.put("/{category_id}", response_model=CategoryDTO, response_model_exclude_none=True)
def update_category(category_id: str, payload: CategoryUpdateDTO) -> CategoryDTO:
    """更新分类注册表中的展示信息。"""
    return category_service.update_category(category_id, payload)
