"""Docusaurus 站点配置对账相关 DTO。"""

from typing import Literal

from pydantic import BaseModel, Field


class DocusaurusConfigNavItemDTO(BaseModel):
    """``navbar.items`` 中一个含 ``to:`` 的导航项及其内容存在性校验结果。"""

    to: str
    label: str | None = None
    dropdown_label: str | None = None  # 所属 dropdown 的 label；顶层项为 None
    exists: bool | None = None  # True/False 为校验结果；None 表示不校验（自定义页面/外链）


class DocsTopCategoryNavDTO(BaseModel):
    """一个未登记到知识库 navbar 的 docs 一级分类。"""

    slug: str
    label: str


class BlogTopCategoryNavDTO(BaseModel):
    """一个未登记到博客 navbar 的 blog 一级分类。"""

    slug: str
    label: str


class DocusaurusConfigStatusDTO(BaseModel):
    """``docusaurus.config.ts`` navbar 与 docs/blog 实际内容的对账状态。"""

    config_exists: bool
    config_path: str
    nav_item_total: int
    nav_items: list[DocusaurusConfigNavItemDTO] = Field(default_factory=list)
    broken_to_links: list[DocusaurusConfigNavItemDTO] = Field(default_factory=list)
    docs_top_category_total: int
    docs_top_categories_missing_in_nav: list[DocsTopCategoryNavDTO] = Field(default_factory=list)
    blog_top_category_total: int = 0
    blog_top_categories_missing_in_nav: list[BlogTopCategoryNavDTO] = Field(default_factory=list)
    stale_blog_nav_items: list[DocusaurusConfigNavItemDTO] = Field(default_factory=list)


class DocusaurusConfigSyncDTO(BaseModel):
    """同步 docusaurus.config.ts navbar 请求 DTO。"""

    mode: Literal["append_missing_top", "remove_broken", "all"] = "all"
    dry_run: bool = True
    confirm: bool = False
