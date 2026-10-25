# data — AGENTS.md

> 运行时数据目录。详细规范见 `admin/lc-docs/PROJECT_STRUCTURE.md`。

## 内容

- `content-schema/`：内容规则中心（分类/标签/Front Matter 模板）
- `ai-models.json`：AI 模型配置
- `registry_index.sqlite3`：可重建的查询索引（派生数据）

## 约定

- YAML/Markdown 是事实源；SQLite 索引可删除重建，不承载事实源语义。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
