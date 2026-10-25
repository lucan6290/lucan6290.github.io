# infrastructure/registry — AGENTS.md

> 注册表与 SQLite 索引。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md` 第 14/15 节。

## 职责

YAML 注册表（分类/标签）与 SQLite 查询索引的读写与重建，是唯一直接访问 SQLite/YAML 的层。

## 内容

- `registry_sqlite_repository.py` / `registry_sqlite_queries.py` / `registry_sqlite_schema.py` / `registry_sqlite_mappers.py`：SQLite 访问与映射。
- `registry_*_indexer.py`：分类/标签/文章索引器。
- `registry_yaml_service.py` / `registry_index_service.py` / `schema_service.py`：注册表与索引服务。
- `tag_service.py` / `tag_registry_service.py` / `tag_slug_service.py`：标签能力。

## 约定

- 存储记录 ↔ DTO 映射显式、集中（`registry_sqlite_mappers.py` 的 `item_from_row`）。
- SQLite 索引可删除重建，不承载事实源语义。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
