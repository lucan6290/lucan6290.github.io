# services/content/sync — AGENTS.md

> 后端索引/站点配置同步。

## 内容

- `backend_index_sync_service.py`：后端索引同步
- `site_config_sync_service.py`：站点配置同步
- `site_content_scanner.py`：站点内容扫描

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
