# services/content — AGENTS.md

> 内容业务服务。详细规范见 `admin/lc-docs/BACKEND_CONVENTION.md`。

## 职责

文章/分类/标签/侧边栏/同步/校验等内容域业务能力。

## 子模块

- `articles/`：文章业务
- `blog/`：博客首页/导航/作者
- `categories/`：分类业务
- `docusaurus/`：Docusaurus 配置
- `sidebars/`：侧边栏
- `sync/`：同步
- `validation/`：校验

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `admin/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
