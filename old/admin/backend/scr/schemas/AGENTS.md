# schemas — AGENTS.md

> 请求/响应 DTO 层（Pydantic）。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md`。

## 职责

接口输入输出对象，负责 Pydantic boundary 的请求校验与响应序列化。

## 内容

每业务域一个文件：agent / article / auth / build / category / common / deploy / docusaurus_config / git_sync / registry_index / schema / sidebar / sync / tag / validation。

## 约定

- DTO 以 `DTO` 结尾；请求 `XxxCreateDTO` / `XxxUpdateDTO`，动作 `XxxRequestDTO`，结果 `XxxResultDTO`。
- 与领域模型（`models/`）分离（`dto_separation`）。
- API 字段 snake_case。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
