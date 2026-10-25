# services/content/blog — AGENTS.md

> 博客首页/导航/作者/内容同步。

## 内容

- `blog_index_service.py`：博客首页分类目录
- `blog_nav_service.py`：博客顶部导航
- `blog_author_service.py`：作者
- `blog_content_sync_service.py`：博客内容同步

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
