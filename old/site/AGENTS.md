# site — AGENTS.md

> 公开站点模块导航入口（Engineering Governance 生成）。详细规范见 `site/lc-docs/FRONTEND_CONVENTION.md`（项目根）。

## 职责

箓川码笺公开博客站点（Docusaurus 3 + React 19 + TypeScript），承载博客/知识库/项目展示，构建后部署在 GitHub 供读者访问。

## 结构

- `blog/`、`docs/`：内容事实源（Markdown/MDX，内容目录不生成模块 AGENTS.md）
- `src/`：站点代码（组件/页面/主题覆写/样式）
- `plugins/`：站点插件
- `static/`：静态资源
- `docusaurus.config.ts`、`sidebars.ts`、`blogSidebars.ts`：导航/配置源

## 启动

```powershell
npm run dev
```

访问 `http://127.0.0.1:3400/`。

## 入口

- 项目导航：项目根 `AGENTS.md`
- 前端规范：`site/lc-docs/FRONTEND_CONVENTION.md`

## 维护要求

新增本目录下的子模块时，必须同步生成该子目录的 `AGENTS.md`，并登记到 `site/lc-docs/DOCUMENTATION_INDEX.md` 的层级索引与根 `AGENTS.md` 的 Task Routing。
