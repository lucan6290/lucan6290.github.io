# services/ai — AGENTS.md

> AI 写作辅助。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md`。

## 职责

AI 写作/编辑/知识库 Agent 与模型配置。

## 子模块

- `editor/`：编辑器 Agent
- `knowledge/`：知识库 QA Agent
- `tools/`：编辑器工具集
- `writing/`：写作 Agent
- `llm_adapter.py`：LLM 适配
- `model_config_service.py`：AI 模型配置

## 约定

- Agent 编排依赖 LLMAdapter + 模型配置。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
