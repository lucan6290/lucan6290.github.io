# utils — AGENTS.md

> 纯函数工具。详细规范见 `admin/lc-docs/FRONTEND_CONVENTION.md` 第 7 节。

## 职责

无副作用的纯函数，可单测。

## 内容

- `auth.ts`：会话管理
- `frontmatter.ts`：Front Matter 解析
- `postDisplay.ts`：文章展示派生
- `approvalPolicy.ts`：审批策略
- `aiWritingValidation.ts`：AI 写作校验

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
