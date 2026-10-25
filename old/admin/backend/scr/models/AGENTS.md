# models — AGENTS.md

> 领域模型层。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md` 第 13 节。

## 职责

存放业务概念（枚举、值对象），区别于 `schemas/` 的对外 DTO。

## 内容

- `article.py`：`ArticleType` 枚举（docs/blog），继承 `str, Enum`。

## 约定

- 领域枚举继承 `str, Enum`，可 JSON 序列化并参与查询参数校验。
- 不直接作为 API 响应（`orm_leaking_to_api` 反模式）。

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
