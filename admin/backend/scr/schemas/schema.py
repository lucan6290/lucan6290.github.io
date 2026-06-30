"""内容 Schema 相关 DTO。"""

from typing import Any

from pydantic import BaseModel, Field

from scr.schemas.category import CategoryDTO
from scr.schemas.tag import TagDTO


class ContentSchemaDTO(BaseModel):
    """内容 Schema 汇总响应 DTO。"""

    categories: list[CategoryDTO] = Field(default_factory=list)
    tags: list[TagDTO] = Field(default_factory=list)
    frontmatter: dict[str, Any] = Field(default_factory=dict)


class SchemaInitDTO(BaseModel):
    """初始化内容 Schema 请求 DTO。"""

    overwrite: bool = False
    dry_run: bool = True
    confirm: bool = False


class SchemaInitResultDTO(BaseModel):
    """初始化内容 Schema 执行结果 DTO。"""

    created: list[str] = Field(default_factory=list)
    overwritten: list[str] = Field(default_factory=list)
    skipped: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
