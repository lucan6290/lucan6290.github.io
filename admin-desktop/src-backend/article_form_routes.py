from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from article_form import form_fields, patch_fields
from article_frontmatter import ArticleError
from content_store import ContentError


class FormInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    raw_content: str = Field(max_length=4_000_000)


class FormValues(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    description: str
    tags: list[str]
    sticky: StrictBool


class FormPatch(FormInput):
    values: FormValues


def create_article_form_router():
    router = APIRouter(prefix="/api/v1/article-form")

    @router.post("/read")
    def read(payload: FormInput):
        try:
            return form_fields(payload.raw_content)
        except ArticleError as error:
            raise ContentError(400, "invalid_article_form", str(error)) from error

    @router.post("/patch")
    def patch(payload: FormPatch):
        try:
            return {"raw_content": patch_fields(payload.raw_content, payload.values.model_dump())}
        except ArticleError as error:
            raise ContentError(400, "invalid_article_form", str(error)) from error

    return router
