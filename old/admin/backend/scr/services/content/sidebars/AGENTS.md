# services/content/sidebars — AGENTS.md

> 侧边栏服务（docs/blog）。

## 内容

- `sidebar_service.py`：docs 侧边栏
- `sidebar_management_service.py`：侧边栏管理
- `sidebar_parser_service.py`：解析
- `sidebar_placement_service.py`：插入位置
- `blog_sidebar_service.py`：blog 侧边栏

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
