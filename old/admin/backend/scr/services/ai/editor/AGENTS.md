# services/ai/editor — AGENTS.md

> 编辑器 AI Agent。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md`。

## 职责

编辑器文章编辑 Agent（运行、审批恢复）。

## 内容

- `agent_service.py`：`EditorAgentService`（含 `PendingApproval`）
- `langchain_agent.py`：`EditorLangChainAgentRunner`（可选增强）

## 约定

- LangChain 为可选依赖，缺失时走轻量 LLM 兜底路径。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
