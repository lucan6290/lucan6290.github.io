# services/ai/tools — AGENTS.md

> 编辑器 Agent 工具集。

## 职责

编辑器 Agent 调用的工具（读/写/预览文章、获取选区等）。

## 内容

editor_article_runtime / editor_operation / editor_toolkit / get_current_selection / preview_current_article_edit / propose_article_edit / read_current_article / write_current_article。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
