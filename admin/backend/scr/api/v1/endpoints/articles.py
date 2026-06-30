"""文章端点。

提供文章创建、文章列表、文章详情与保存接口。
"""

import mimetypes

from fastapi import APIRouter, File, Form, Query, UploadFile
from fastapi.responses import FileResponse

from scr.models.article import ArticleType
from scr.schemas.article import (
    ArticleCreateDTO,
    ArticleDetailDTO,
    ArticleImageCheckDTO,
    ArticleImageListDTO,
    ArticleListResponseDTO,
    ArticleMoveDTO,
    ArticleUpdateDTO,
    ArticleValidationResultDTO,
    ImageDTO,
)
from scr.schemas.common import MutationPlanDTO
from scr.services.content.article_service import ArticleService


router = APIRouter(prefix="/articles", tags=["articles"])
article_service = ArticleService()  # 模块级单例，复用底层服务与缓存能力


@router.get("", response_model=ArticleListResponseDTO)
def list_articles(
    article_type: ArticleType | None = Query(default=None, alias="type"),
    keyword: str | None = None,
    tag: str | None = None,
    author: str | None = None,
    category: str | None = None,
    has_issues: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort: str | None = None,
) -> ArticleListResponseDTO:
    """获取文章摘要分页列表。"""
    return article_service.list_articles(
        article_type=article_type,
        keyword=keyword,
        tag=tag,
        author=author,
        category=category,
        has_issues=has_issues,
        page=page,
        page_size=page_size,
        sort=sort,
    )


@router.post("", response_model=ArticleDetailDTO, status_code=201)
def create_article(payload: ArticleCreateDTO) -> ArticleDetailDTO:
    """创建 docs 或 blog 文章，并返回创建后的文章详情。"""
    return article_service.create_article(payload)


@router.get("/{article_id}", response_model=ArticleDetailDTO)
def get_article(article_id: str) -> ArticleDetailDTO:
    """按文章 ID 获取详情；ID 由 ArticleService 的 base64 编码规则生成。"""
    return article_service.get_article(article_id)


@router.put("/{article_id}", response_model=ArticleDetailDTO)
def save_article(article_id: str, payload: ArticleUpdateDTO) -> ArticleDetailDTO:
    """保存文章 Front Matter 与正文，不改变文章路径。"""
    return article_service.save_article(article_id, payload)


@router.delete(
    "/{article_id}",
    response_model=MutationPlanDTO,
    response_model_exclude_none=True,
)
def delete_article(
    article_id: str,
    with_images: bool = Query(default=False),
    dry_run: bool = Query(default=True),
    confirm: bool = Query(default=False),
) -> MutationPlanDTO:
    """删除文章文件；默认只返回影响分析，执行删除需要显式确认。"""
    return article_service.delete_article(
        article_id,
        with_images=with_images,
        dry_run=dry_run,
        confirm=confirm,
    )


@router.post(
    "/{article_id}/move",
    response_model=MutationPlanDTO,
    response_model_exclude_none=True,
)
def move_article(article_id: str, payload: ArticleMoveDTO) -> MutationPlanDTO:
    """移动或重命名文章；默认只返回影响分析，执行移动需要显式确认。"""
    return article_service.move_article(article_id, payload)


@router.post("/{article_id}/validate", response_model=ArticleValidationResultDTO)
def validate_article(article_id: str) -> ArticleValidationResultDTO:
    """校验单篇文章的 Front Matter、侧边栏登记与本地图片引用。"""
    return article_service.validate_article(article_id)


@router.get("/{article_id}/images", response_model=ArticleImageListDTO)
def list_article_images(article_id: str) -> ArticleImageListDTO:
    """获取文章同名图片目录中的图片列表。"""
    return article_service.list_article_images(article_id)


@router.post("/{article_id}/images/check", response_model=ArticleImageCheckDTO)
def check_article_images(article_id: str) -> ArticleImageCheckDTO:
    """检查文章图片引用与图片目录之间的差异。"""
    return article_service.check_article_images(article_id)


@router.get("/{article_id}/images/{image_name}/content")
def get_article_image_content(article_id: str, image_name: str) -> FileResponse:
    """读取文章同名图片目录中的图片内容，用于编辑器预览。"""
    image_path = article_service.get_article_image_path(article_id, image_name)
    media_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
    return FileResponse(image_path, media_type=media_type, filename=image_path.name)


@router.post("/{article_id}/images", response_model=ImageDTO, status_code=201)
async def upload_article_image(
    article_id: str,
    file: UploadFile = File(...),
    slug: str | None = Form(default=None),
    alt: str | None = Form(default=None),
) -> ImageDTO:
    """上传文章图片到文章同名图片目录。"""
    content = await file.read()
    return article_service.upload_article_image(
        article_id,
        original_filename=file.filename or "",
        content_type=file.content_type,
        content=content,
        slug=slug,
        alt=alt,
    )


@router.delete(
    "/{article_id}/images/{image_name}",
    response_model=MutationPlanDTO,
    response_model_exclude_none=True,
)
def delete_article_image(
    article_id: str,
    image_name: str,
    dry_run: bool = Query(default=True),
    confirm: bool = Query(default=False),
) -> MutationPlanDTO:
    """删除文章图片；默认只返回影响分析，执行删除需要显式确认。"""
    return article_service.delete_article_image(
        article_id,
        image_name,
        dry_run=dry_run,
        confirm=confirm,
    )
