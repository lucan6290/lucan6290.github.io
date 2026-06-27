# 博客管理后台

箓川码笺博客的管理端代码统一放在 `admin-dev/`，目录只保留三块：

```text
admin-dev/
├── frontend/  # Vue 3 + Vite 管理后台前端
├── backend/   # Python FastAPI 后端
└── docs/      # 管理端文档
```

## 功能

- 文章管理：创建、编辑、删除博客文章
- Markdown 编辑器：基于 ByteMD 的实时编辑体验，支持 GFM、代码高亮、数学公式、Mermaid 图表和 Hexo/Butterfly 标签预览
- Front Matter 编辑：可视化编辑文章元数据
- 媒体资源管理：上传和管理文章图片
- 分类与标签：管理文章分类和标签；新增一级分类时会同步创建文章目录、默认封面、Hexo `category_map` 映射和文章总目录占位
- AI 助手：辅助写作、润色和生成内容
- AI 辅助写作：支持 Agent 草稿方案、结构化编辑操作和本地知识库问答
- 直接文件管理：通过 FastAPI 后端读写博客内容

## 技术栈

前端：

- Vue 3 + TypeScript
- Vite 8
- Vue Router
- Pinia
- Naive UI
- ByteMD

后端：

- Python
- FastAPI
- Uvicorn

## 开发命令

### 前端

```bash
cd admin-dev/frontend
npm install
npm run dev
```

前端默认访问地址：

```text
http://localhost:14000/admin/
```

### 后端

```bash
cd admin-dev/backend
.venv/Scripts/python.exe main.py
```

后端默认地址：

```text
http://localhost:15000
```

API 文档：

```text
http://localhost:15000/docs
```

### AI 辅助写作相关接口

后端新增结构化 AI 写作接口：

```text
GET  /api/files/category-registry
POST /api/ai/writing/agent/plan
POST /api/ai/writing/agent/commit
POST /api/ai/writing/edit/plan
POST /api/ai/writing/edit/apply
POST /api/files/article-index/scan
GET  /api/files/article-index
POST /api/ai/knowledge-qa
```

其中文章创建和保存仍复用统一文章接口；知识库问答只读取本地 Markdown 和可重建缓存，不会写入文章、发布、部署或执行 Git 操作。

### 同时启动前后端

```bash
cd admin-dev
.\start-dev.ps1
```

也可以使用前端目录中的 Node 启动脚本：

```bash
cd admin-dev/frontend
npm run dev:all
```

### 构建前端

```bash
cd admin-dev/frontend
npm run build
```

构建产物会输出到博客静态目录：

```text
blog-content/source/admin/
```

不要直接手动修改 `blog-content/source/admin/`，它是构建产物。

## 配置文件

前端配置模板：

```text
admin-dev/frontend/.env.development
```

后端配置模板：

```text
admin-dev/backend/.env.development
```

后端实际运行配置：

```text
admin-dev/backend/.env
```

`backend/.env` 可包含本地开发配置，不应提交到仓库。

## AI 模型配置

管理后台会默认提供 DeepSeek V4 Pro 和 DeepSeek V4 Flash 两个配置项，对应 DeepSeek `/models` 当前返回的可用模型：

- Base URL：`https://api.deepseek.com`
- Model ID：`deepseek-v4-pro`、`deepseek-v4-flash`
- Anthropic Base URL：`https://api.deepseek.com/anthropic`
- 思考模式：开启，V4 Pro 默认推理强度 `max`，V4 Flash 默认 `high`
- 能力标记：Agent 模式、Tool Calls、JSON Output

首次使用前，需要在“设置 / AI 配置”中编辑该模型并填入自己的 DeepSeek API Key。旧的 `deepseek-chat` / `deepseek-reasoner` 本地配置会在加载时迁移到 `deepseek-v4-pro`。

实现说明：

- 本系统实际调用路径仍使用 OpenAI 兼容的 `/chat/completions`。
- Agent 草稿方案、结构化编辑和 JSON 修复请求会启用 `response_format: { "type": "json_object" }`。
- 普通对话、知识库回答不强制 JSON Output。
- 多轮对话由前端维护 messages 历史并随请求回传；DeepSeek API 本身是无状态的。
- 上下文硬盘缓存由 DeepSeek 默认开启，系统不需要额外传参；稳定的 system prompt 和连续 messages 前缀有利于命中缓存。
- Anthropic Base URL 作为模型配置元数据展示，用于 Claude Code / Anthropic SDK 生态；管理后台自身暂不走 Anthropic Messages API。

## 关键路径

- 前端源码：`admin-dev/frontend/src/`
- 前端入口：`admin-dev/frontend/src/main.ts`
- 前端构建配置：`admin-dev/frontend/vite.config.ts`
- 后端入口：`admin-dev/backend/main.py`
- 后端应用：`admin-dev/backend/app/main.py`
- 后端配置：`admin-dev/backend/app/config.py`

## 使用流程

1. 启动后端：`cd admin-dev/backend && .venv/Scripts/python.exe main.py`
2. 启动前端：`cd admin-dev/frontend && npm run dev`
3. 打开 `http://localhost:14000/admin/`
4. 直接进入管理后台

## 编辑器预览能力

管理端编辑器预览支持以下内容：

- 标准 Markdown：标题、列表、引用、链接、图片、代码块等
- GFM 扩展：表格、任务列表、删除线等
- 代码高亮
- Front Matter 识别
- 数学公式：行内 `$...$` 和块级 `$$...$$`
- Mermaid 图表：标准 fenced code block，例如 ```` ```mermaid ````
- Hexo/Butterfly 标签：在预览区以语义块或行内标签展示，不改写原始 Markdown

Hexo/Butterfly 标签预览是编辑期辅助展示，最终页面效果仍以 Hexo 构建和 Butterfly 主题渲染为准。

### 图片插入流程

编辑器支持直接粘贴、拖拽或通过编辑器图片按钮选择图片：

1. 前端调用本地后端 `POST /api/assets/image`
2. 后端把图片保存到当前文章同名资源文件夹
3. 编辑器自动插入相对路径 Markdown，例如 `![图片说明](文章名-img1.png)`
4. 预览区通过 `GET /api/assets/file/{path}` 临时读取图片，最终 Markdown 仍保持 Hexo 友好的相对路径

这种方式兼容 Hexo `post_asset_folder`，无需作者手动创建资源目录或复制图片路径。

图片上传是立即落盘的。保存文章时，后端会扫描当前 Markdown 中实际引用的图片，并和文章资源目录中的图片对比：

- 如果没有未引用图片，正常保存
- 保存文章或点击“清理资源”时，会扫描当前 Markdown 引用的图片
- 清理时会直接删除未引用图片，不再移动到 `_unused/`
- 编辑器工具栏中的「清理资源」可以随时手动扫描和清理未引用图片

## 部署流程

1. 在 `admin-dev/frontend` 运行 `npm run build`
2. 在博客根目录运行 `npm run build`
3. 推送到 GitHub 后由 GitHub Actions 部署

## 开发注意

- `admin-dev` 根目录只放 `frontend/`、`backend/`、`docs/`
- 前端依赖和构建脚本都在 `frontend/`
- 后端虚拟环境和 API 代码都在 `backend/`
- 文档放在 `docs/`
- 修改管理端前端时，构建后会更新 `blog-content/source/admin/`
