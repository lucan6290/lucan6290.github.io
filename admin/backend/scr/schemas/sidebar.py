"""侧边栏相关 DTO。"""

from typing import Literal

from pydantic import BaseModel, Field


SidebarTargetType = Literal["docs", "blog"]


class BlogSidebarCategoryDTO(BaseModel):
    """blog 侧边栏中的一级分类项。"""

    label: str
    path: str
    to: str
    count: int | None = None
    collapsed: bool | None = None
    items: list[dict[str, str]] = Field(default_factory=list)


class SidebarStatusDTO(BaseModel):
    """侧边栏对账状态响应 DTO。"""

    type: SidebarTargetType = "docs"
    sidebars_exists: bool
    sidebars_path: str | None = None
    docs_count: int
    registered_count: int
    missing_count: int
    orphan_count: int
    registered_doc_ids: list[str]
    missing_in_sidebars: list[str]
    orphan_sidebar_ids: list[str]
    blog_category_count: int | None = None
    registered_categories: list[BlogSidebarCategoryDTO] = Field(default_factory=list)
    missing_blog_categories: list[BlogSidebarCategoryDTO] = Field(default_factory=list)
    orphan_blog_sidebar_items: list[BlogSidebarCategoryDTO] = Field(default_factory=list)


class SidebarSyncDTO(BaseModel):
    """同步 docs/blog 侧边栏请求 DTO。"""

    type: SidebarTargetType = "docs"
    mode: Literal["append_missing", "regenerate", "sync_categories"] = "append_missing"
    dry_run: bool = True
    confirm: bool = False


class DocsIndexSyncDTO(BaseModel):
    """同步 docs 一级分类目录页请求 DTO。"""

    dry_run: bool = True
    confirm: bool = False


class BlogIndexSyncDTO(BaseModel):
    """同步 blog 首页文档请求 DTO。"""

    dry_run: bool = True
    confirm: bool = False
