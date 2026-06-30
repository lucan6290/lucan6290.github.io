"""侧边栏相关 DTO。"""

from typing import Literal

from pydantic import BaseModel


class SidebarStatusDTO(BaseModel):
    """侧边栏对账状态响应 DTO。"""

    sidebars_exists: bool
    docs_count: int
    registered_count: int
    missing_count: int
    orphan_count: int
    registered_doc_ids: list[str]
    missing_in_sidebars: list[str]
    orphan_sidebar_ids: list[str]


class SidebarSyncDTO(BaseModel):
    """同步 docs 侧边栏请求 DTO。"""

    mode: Literal["append_missing", "regenerate"] = "append_missing"
    dry_run: bool = True
    confirm: bool = False
