# infrastructure — AGENTS.md

> 基础设施层。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md` 第 14 节。

## 职责

文件系统与注册表/SQLite 等基础能力，是唯一直接访问存储的层，不 import services。

## 子模块

- `filesystem/`：文件与 Markdown 基础能力。
- `registry/`：YAML 注册表 + SQLite 查询索引。

## 约定

- 不泄漏 SQLite 行/SQL/文件句柄到上层。
- SQLite 索引是可删除重建的派生数据。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
