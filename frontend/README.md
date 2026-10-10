# frontend — 箓川码笺自研前端

> 替代 `site/`（Docusaurus）的自研前端，页面样式完全复刻现站，代码独立编写。

## 技术栈

- Vite 6 + Vue 3.5 + TypeScript
- ByteMD（GFM + highlight + KaTeX + Mermaid）只读渲染
- minisearch 全文搜索
- 纯 CSS design tokens（复刻 site/src/css/custom.css 变量体系）

## 本地开发

```powershell
cd frontend
pnpm install
pnpm dev          # http://127.0.0.1:3400/
```

端口固定为 **3400**（遵守项目根 AGENTS.md 约束）。若被占用先清理：

```powershell
netstat -ano | Select-String ':3400'
Stop-Process -Id <PID> -Force
```

## 内容写作规范

- 内容事实源：`content/` 目录
- 目录 = 分类页，`.md` = 内容页，任意嵌套
- 文件名数字前缀排序：`01-xxx.md`；无前缀按 mtime
- frontmatter 字段：`title` / `date` / `updated` / `tags` / `description` / `sticky`
- 置顶：`sticky: true` 恒排最前
- 新建目录/文件即自动出现在导航，**零配置**

## 顶部导航映射

编辑 `src/config/nav.ts`，新增分区只需追加一条 `NavEntry`。

## 构建

```powershell
pnpm build        # 输出到 dist/
pnpm preview      # 本地预览构建产物
```

## 不在本前端范围

- 评论区 / 阅读统计（P1）
- SEO / RSS / SSG 预渲染（P2）
- series 系列专题
- 在线编辑 / admin 联动
- 内容迁移（用户自行从 site/blog + site/docs 迁入）
