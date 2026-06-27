# AI 辅助写作后端技术文档

## 1. 文档目标

本文档依据 `admin-dev/docs/ai-writing-assistant-requirements.md` 编写，面向后端开发实现，覆盖 AI 辅助写作页面所需的接口设计、本地文件扫描、文章创建与更新、LangChain/LangGraph 编排、提示词模板、schema 校验、知识库索引缓存、异常处理和安全边界。

本功能属于博客管理后台后端能力扩展，目标是在不引入长期运行数据库服务、不绕过现有文章规范、不直接修改主题源码的前提下，为前端提供稳定、可审计、可恢复的 AI 写作工作流。

## 2. 现有后端基础

当前管理后台后端位于 `admin-dev/backend/`，技术栈为 Python + FastAPI。

已有关键能力：

| 能力 | 现有位置 | 说明 |
| --- | --- | --- |
| FastAPI 应用入口 | `app/main.py` | 注册路由、CORS、健康检查 |
| 配置 | `app/config.py` | `BLOG_ROOT`、`POSTS_DIR`、`PREFIX_TO_DIR`、模型预设 |
| 文章列表和详情 | `app/routers/files.py` | `GET /api/files/posts`、`GET /api/files/post/{path}` |
| 文章创建 | `app/routers/files.py` | `POST /api/files/post`，内部调用 `npx hexo np` |
| 文章更新 | `app/routers/files.py` | `PUT /api/files/post/{path}`，负责 Front Matter 合并和正文写入 |
| Front Matter 解析 | `app/services/frontmatter.py` | 解析、生成、分类扁平化 |
| 目录索引同步 | `app/services/index_updater.py` | `index.md` 纯函数更新引擎 |
| AI 基础对话 | `app/routers/ai.py` | `POST /api/ai/chat`，使用 LangChain + ChatOpenAI + SSE |
| 资源图片管理 | `app/routers/assets.py`、`app/services/assets.py` | 上传、读取、清理未引用图片 |

后续实现必须优先复用以下统一接口：

- 创建文章：`POST /api/files/post`
- 更新文章：`PUT /api/files/post/{path}`
- 读取文章：`GET /api/files/post/{path}`
- 获取文章列表：`GET /api/files/posts`

AI 工作流不得绕过这些接口直接写入文章文件。确需抽取公共服务时，应从现有路由中提炼服务函数，再由路由和 AI 编排共同调用同一服务。

## 3. 后端模块规划

建议新增如下模块：

```text
admin-dev/backend/app/
├── routers/
│   ├── ai_writing.py          # Agent / LLM 结构化写作接口
│   └── article_index.py       # 本地文章索引扫描和读取接口
├── services/
│   ├── ai_models.py           # LLM 实例构建、模型配置校验
│   ├── ai_prompts.py          # 提示词模板
│   ├── ai_schemas.py          # AI 输出 Pydantic schema
│   ├── ai_validation.py       # schema 和业务校验
│   ├── ai_graphs.py           # LangGraph 编排
│   ├── article_scanner.py     # 本地 Markdown 扫描
│   ├── article_index_cache.py # 本地索引缓存读写和失效判断
│   ├── knowledge_retriever.py # 关键词检索、分块检索、引用校验
│   └── safety.py              # 权限模式、风险降级、安全边界
└── schemas.py                 # 可继续放通用请求响应；复杂 AI schema 建议独立
```

缓存目录：

```text
admin-dev/.cache/
├── article-index.json
├── article-chunks.json
└── ai-writing-sessions.jsonl  # 可选，仅记录后端任务流水；前端历史仍以 localStorage 为主
```

`.cache` 为可删除、可重建目录，不作为唯一事实来源。

## 4. 核心数据模型

### 4.1 通用响应

继续沿用现有 `ApiResponse`：

```ts
interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
}
```

复杂接口的 `data` 中必须包含可供前端恢复 UI 状态的信息，避免异常后丢失用户输入和已生成方案。

### 4.2 权限模式

```ts
type AIApprovalMode = 'request-approval' | 'delegate-approval' | 'full-access'
```

后端必须独立校验权限模式，不能只信任前端 UI。

自动执行能力：

| 权限模式 | 后端允许自动执行 | 后端必须阻断或降级 |
| --- | --- | --- |
| `request-approval` | 只生成方案、预览、编辑建议 | 任何创建、写入、删除、发布、Git、部署 |
| `delegate-approval` | 低风险、schema 通过、置信度达标时创建草稿或小范围修改 | 删除、全文重写、改一级分类、低置信度、高风险、求证未完成 |
| `full-access` | 当前 AI 写作任务内自动创建草稿、写正文、当前文章内编辑 | 发布、部署、Git、删除文件、改主题源码、改系统配置、创建未注册一级分类、执行命令 |

风险降级规则：

- `confidence < 0.6`，降级为 `request-approval`。
- `clarificationRequired = true`，降级为 `request-approval`。
- `riskFlags` 包含 `分类不确定`、`事实待验证`、`信息不足`、`可能包含敏感信息`，降级为 `request-approval`。
- 图片占位无法确认、作用范围不明确、schema 校验失败、业务校验失败，均降级为 `request-approval`。

### 4.3 分类注册表

后端以 `app/config.py` 中的 `PREFIX_TO_DIR` 为基础事实源：

```ts
interface CategoryRegistryItem {
  prefix1: 'ts' | 'pr' | 'pp' | 'ge' | 'rs'
  primaryName: string
  primarySlug: string
  dir: string
  cover: string
}
```

示例：

```json
{
  "prefix1": "ts",
  "primaryName": "技术研习",
  "primarySlug": "tech-study",
  "dir": "tech-study",
  "cover": "/img/covers/tech-study.svg"
}
```

一级分类只能来自注册表。AI 不允许生成新一级分类。

### 4.4 Agent 草稿方案

```ts
interface AIDraftPlan {
  schemaVersion: string
  approvalMode: AIApprovalMode
  writingGoal: 'auto' | 'blog-draft' | 'study-note' | 'pitfall-review' | 'project-log' | 'thought-essay' | 'resource-digest' | 'outline-expansion'
  userIntent: string
  inputType: string
  clarificationRequired: boolean
  clarificationQuestions: string[]
  primarySlug: string
  primaryName: string
  prefix1: string
  prefix2: string
  title: string
  tags: string[]
  description: string
  outline: string[]
  imagePlaceholders: string[]
  bodyMarkdown: string
  missingInfoQuestions: string[]
  riskFlags: string[]
  confidence: number
  reviewChecklist: string[]
  rationale: string
}
```

后端建议使用 Pydantic 定义同名模型，并设置枚举、长度和类型约束。

### 4.5 LLM 编辑操作

```ts
interface AIEditOperation {
  type: 'insert' | 'replace' | 'delete' | 'rewrite' | 'frontmatter'
  scope: 'selection' | 'cursor' | 'document' | 'frontmatter'
  approvalMode: AIApprovalMode
  requiresManualApproval: boolean
  summary: string
  oldText?: string
  newText?: string
  frontMatterPatch?: Record<string, unknown>
  riskFlags: string[]
  confidence: number
}
```

后端只返回结构化编辑操作。是否应用编辑，由权限模式、风险校验和前端确认共同决定。真正保存仍调用 `PUT /api/files/post/{path}`。

### 4.6 本地文章索引

```ts
interface ArticleIndexItem {
  path: string
  fileName: string
  title: string
  date?: string
  updated?: string
  categories: string[][]
  tags: string[]
  status?: 'draft' | 'wip' | 'published'
  published?: boolean
  description?: string
  headings: string[]
  excerpt: string
  mtime: string
  contentHash: string
}

interface ArticleChunk {
  id: string
  articlePath: string
  articleTitle: string
  headingPath: string[]
  text: string
  startLine?: number
  endLine?: number
  contentHash: string
}
```

索引只作为加速缓存。知识库回答前必须确认索引仍对应本地文件。

## 5. 接口设计

### 5.1 获取分类注册表

```http
GET /api/files/category-registry
```

响应：

```json
{
  "success": true,
  "data": [
    {
      "prefix1": "ts",
      "primaryName": "技术研习",
      "primarySlug": "tech-study",
      "dir": "tech-study",
      "cover": "/img/covers/tech-study.svg"
    }
  ]
}
```

实现要点：

- 从 `PREFIX_TO_DIR` 动态生成，避免与配置漂移。
- 不读取 AI 输出。
- 不允许前端提交新增一级分类。

### 5.2 Agent 生成草稿方案

```http
POST /api/ai/writing/agent/plan
```

请求：

```json
{
  "sessionId": "uuid",
  "userInput": "今天踩了一个 Docker 容器启动失败的坑...",
  "approvalMode": "request-approval",
  "writingGoal": "auto",
  "userPreferences": {
    "audience": "前端开发者",
    "expectedLength": "medium",
    "style": "技术复盘"
  },
  "clarificationAnswers": []
}
```

图片占位保留不作为单独请求字段传入。后端只根据 `userInput` 中的自然语言要求、Markdown/HTML 图片语法、截图说明、文件名或“此处有图”等内容线索识别图片占位约束。

响应：

```json
{
  "success": true,
  "data": {
    "sessionId": "uuid",
    "plan": {},
    "preview": {
      "fileName": "pr-docker-Docker容器启动失败排查.md",
      "relativePath": "pitfall-review/pr-docker-Docker容器启动失败排查.md",
      "requiresManualApproval": true,
      "approvalModeEffective": "request-approval",
      "downgradeReasons": []
    },
    "validationErrors": [],
    "warnings": []
  }
}
```

职责：

- 收集分类注册表、已有文章、已有二级前缀、最近方案摘要。
- 使用 LangGraph 生成结构化 `AIDraftPlan`。
- 做 JSON 解析、Pydantic schema 校验、业务规则校验和风险降级。
- 只返回方案和预览，不创建文件。

### 5.3 Agent 创建并写入草稿

```http
POST /api/ai/writing/agent/commit
```

请求：

```json
{
  "sessionId": "uuid",
  "approvalMode": "request-approval",
  "confirmed": true,
  "idempotencyKey": "uuid",
  "plan": {}
}
```

响应：

```json
{
  "success": true,
  "data": {
    "path": "pitfall-review/pr-docker-Docker容器启动失败排查.md",
    "created": true,
    "written": true,
    "editorUrl": "/editor?file=pitfall-review%2Fpr-docker-Docker容器启动失败排查.md",
    "warnings": []
  }
}
```

职责：

1. 重新校验 `plan`，禁止使用未校验缓存直接写入。
2. 校验 `confirmed` 与权限模式是否满足写入条件。
3. 校验 `idempotencyKey`，避免重复点击创建重复文件。
4. 调用统一创建文章能力，等价于 `POST /api/files/post`。
5. 创建成功后读取新文章 Front Matter。
6. 合并允许字段并调用统一更新文章能力，等价于 `PUT /api/files/post/{path}`。
7. 返回创建路径和可跳转编辑器地址。

幂等规则：

- 同一 `idempotencyKey` 成功后再次请求，直接返回第一次创建结果。
- 同一 `idempotencyKey` 创建成功但写入失败，再次请求只重试写入，不重新创建文章。
- 幂等记录可保存在内存和 `admin-dev/.cache/ai-writing-sessions.jsonl`，缓存损坏不影响手动重试。

### 5.4 LLM 生成编辑操作

```http
POST /api/ai/writing/edit/plan
```

请求：

```json
{
  "sessionId": "uuid",
  "articlePath": "tech-study/ts-ai-Agent入门.md",
  "instruction": "把选中的段落改得更清楚，但不要新增事实",
  "approvalMode": "request-approval",
  "scope": "selection",
  "selection": {
    "text": "原始选中文本",
    "startLine": 12,
    "endLine": 18
  }
}
```

响应：

```json
{
  "success": true,
  "data": {
    "operation": {
      "type": "replace",
      "scope": "selection",
      "requiresManualApproval": true,
      "summary": "润色选中段落，保持原意",
      "oldText": "原始选中文本",
      "newText": "新文本",
      "riskFlags": [],
      "confidence": 0.86
    },
    "validationErrors": [],
    "warnings": []
  }
}
```

职责：

- 读取当前文章，解析 Front Matter 和正文。
- 明确作用范围：`selection`、`cursor`、`document`、`frontmatter`。
- 调用 LangChain 生成结构化 `AIEditOperation`。
- 校验 `oldText` 是否存在于作用范围内。
- 不直接保存文章，除非后续提供明确的 apply 接口且权限允许。

### 5.5 LLM 应用编辑操作

```http
POST /api/ai/writing/edit/apply
```

请求：

```json
{
  "sessionId": "uuid",
  "articlePath": "tech-study/ts-ai-Agent入门.md",
  "approvalMode": "request-approval",
  "confirmed": true,
  "operation": {}
}
```

响应：

```json
{
  "success": true,
  "data": {
    "path": "tech-study/ts-ai-Agent入门.md",
    "updated": true,
    "unusedImages": []
  }
}
```

职责：

- 重新读取文章，避免基于过期内容覆盖用户新修改。
- 校验 `oldText` 仍存在。
- 应用插入、替换、删除、全文重写或 Front Matter patch。
- 调用统一更新文章接口保存。

冲突处理：

- 如果文章内容变化导致 `oldText` 找不到，返回冲突错误，不自动猜测替换位置。
- 如果 `operation` 是删除、全文重写或高风险 Front Matter 修改，即使是 `full-access` 也必须经过风险校验。

### 5.6 扫描文章索引

```http
POST /api/files/article-index/scan
```

请求：

```json
{
  "includeDrafts": true,
  "force": false
}
```

响应：

```json
{
  "success": true,
  "data": {
    "scannedAt": "2026-06-26T10:00:00+08:00",
    "articleCount": 36,
    "draftCount": 8,
    "indexStatus": "rebuilt",
    "failedFiles": []
  }
}
```

职责：

- 扫描 `blog-content/source/_posts/**/*.md`。
- 可选扫描 `blog-content/source/_drafts/**/*.md`。
- 解析 Front Matter、标题层级、正文纯文本、摘要、mtime、hash。
- 写入 `admin-dev/.cache/article-index.json` 和 `article-chunks.json`。
- 单文件失败时记录失败文件，不中断整体扫描。

### 5.7 获取文章索引

```http
GET /api/files/article-index
```

查询参数：

```text
?includeDrafts=true&autoRefresh=true
```

响应：

```json
{
  "success": true,
  "data": {
    "scannedAt": "2026-06-26T10:00:00+08:00",
    "indexStatus": "fresh",
    "articles": [],
    "stats": {
      "total": 36,
      "byCategory": {},
      "byStatus": {},
      "byTag": {}
    },
    "warnings": []
  }
}
```

职责：

- 缓存存在且新鲜时直接返回。
- 缓存缺失、损坏或过期时自动重建。
- 如果重建失败，返回已知失败原因，不输出伪数据。

### 5.8 知识库问答

```http
POST /api/ai/knowledge-qa
```

请求：

```json
{
  "sessionId": "uuid",
  "question": "我有哪些文章？",
  "forceRescan": false,
  "includeDrafts": true,
  "model": {
    "baseUrl": "",
    "apiKey": "",
    "modelId": ""
  }
}
```

响应：

```json
{
  "success": true,
  "data": {
    "questionType": "inventory",
    "scannedAt": "2026-06-26T10:00:00+08:00",
    "answer": "当前共扫描到 36 篇文章...",
    "citations": [],
    "warnings": []
  }
}
```

职责：

- 只读。
- 对清单统计类问题，直接用本地索引计算事实，不让 LLM 猜数量。
- 对具体内容类问题，先检索正文分块，再让 LLM 基于证据组织回答。
- 找不到依据时必须回答“当前文章中没有找到明确依据”。

## 6. 本地文件扫描设计

### 6.1 扫描范围

默认扫描：

```text
blog-content/source/_posts/**/*.md
blog-content/source/_drafts/**/*.md
```

排除：

- 与文章同名的资源文件夹。
- `node_modules`、`themes`、`public`、`.cache`。
- 非 Markdown 文件。

### 6.2 扫描步骤

1. 递归获取 Markdown 文件路径。
2. 使用 UTF-8 读取文件，去除 BOM。
3. 用 `parse_frontmatter` 解析 Front Matter 和正文。
4. 规范化 `categories` 为二维数组，同时保留扁平分类用于统计。
5. 提取 Markdown 标题层级。
6. 去除代码块、HTML、Markdown 标记后生成纯文本摘要。
7. 按标题和段落生成正文分块。
8. 计算 `contentHash`。
9. 读取文件 `mtime`。
10. 生成索引项和分块项。

### 6.3 文件名解析

文件命名规则：

```text
prefix1-prefix2-title.md
```

解析结果：

```ts
interface ParsedFileName {
  prefix1: string
  prefix2: string
  titleFromFileName: string
  valid: boolean
  warnings: string[]
}
```

规则：

- `prefix1` 必须在 `PREFIX_TO_DIR` 中。
- `prefix2` 不能为空且不能包含 `-`。
- 标题部分允许中文。
- 解析失败不影响文章进入索引，但要加入 `warnings`。

### 6.4 正文分块

分块目标是支持知识库具体内容问答。

规则：

- 优先按 Markdown 标题分块。
- 单块建议 400 到 1200 个中文字符。
- 保留 `headingPath`，例如 `["## 背景", "### 问题现象"]`。
- 记录 `startLine`、`endLine`，方便引用来源。
- 代码块可保留在相邻语义块中，但检索摘要应避免只由代码组成。

### 6.5 index.md 一致性检查

扫描完成后可读取 `blog-content/source/_posts/index.md` 做轻量一致性检查：

- 已发布文章是否出现在 index.md。
- index.md 中是否存在本地不存在的文章链接。
- 分类路径是否与 Front Matter 不一致。

知识库模式以实际文件扫描为准。如果发现不一致，在回答中加入提示：

```text
检测到文章目录索引可能需要同步，以下回答以本地 Markdown 文件扫描结果为准。
```

## 7. 文章创建与更新设计

### 7.1 创建文章

AI Agent 不直接写文件，而是调用统一创建文章能力：

```http
POST /api/files/post
```

请求：

```json
{
  "title": "AI写作助手工作流设计",
  "prefix1": "ts",
  "prefix2": "ai"
}
```

现有实现会执行：

```bash
npx hexo np <prefix1> <prefix2> "标题"
```

后端 AI commit 接口调用前必须校验：

- `title` 非空。
- `prefix1` 在 `PREFIX_TO_DIR` 中。
- `prefix2` 非空。
- `prefix2` 不包含 `-`。
- 预期文件不存在，或通过统一创建接口返回冲突。
- 当前权限模式允许进入创建阶段。

### 7.2 写入 AI 生成正文

创建成功后，AI commit 接口读取返回路径，并调用统一更新文章能力：

```http
PUT /api/files/post/{path}
```

写入字段：

```json
{
  "frontMatter": {
    "title": "AI写作助手工作流设计",
    "categories": [["技术研习", "ai"]],
    "tags": ["AI", "写作助手"],
    "description": "本文整理 AI 写作助手后端工作流...",
    "layout": "post",
    "comments": true,
    "published": true,
    "lang": "zh-CN",
    "cover": "/img/covers/tech-study.svg",
    "status": "draft"
  },
  "content": "## 背景\n\n..."
}
```

注意：

- `content` 只传正文，不包含 Front Matter。
- `bodyMarkdown` 中禁止出现 Front Matter 分隔符 `---`。
- `status` 默认 `draft`。
- `cover` 来自分类注册表。
- `categories` 使用 `[[一级分类中文名, 二级前缀]]`。
- `updated` 由现有更新接口自动维护。

### 7.3 创建成功但写入失败

处理方式：

- 返回 `created: true`、`written: false`。
- 返回已创建文章路径。
- 不尝试删除已创建文章。
- 前端提示用户可进入编辑器手动恢复。
- 幂等重试时只重试写入，不重复创建。

### 7.4 LLM 模式更新文章

LLM 模式只在应用编辑操作时保存：

1. 后端重新读取文章。
2. 校验编辑操作仍能应用。
3. 生成新正文和 Front Matter patch。
4. 调用统一更新文章能力。

允许修改的 Front Matter 字段：

- `title`
- `description`
- `tags`
- `categories`，但改一级分类必须人工确认
- `series`
- `series_order`
- `excerpt`
- `slug`
- `status`，但不能自动改为 `published`

禁止自动修改：

- `date`
- `layout`
- `comments`
- `published`
- `lang`
- `cover`，除非一级分类修改已人工确认
- `permalink`
- `sticky`

## 8. LangChain / LangGraph 编排

### 8.1 模型构建

统一模型构建函数：

```py
def build_chat_model(config: ModelConfig, *, streaming: bool = False) -> ChatOpenAI:
    return ChatOpenAI(
        base_url=config.base_url,
        api_key=config.api_key,
        model=config.model_id,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        streaming=streaming,
    )
```

校验：

- `baseUrl`、`apiKey`、`modelId` 不能为空。
- `temperature` 建议 Agent 模式使用 `0.2` 到 `0.5`。
- JSON 输出节点建议关闭过高随机性。

### 8.2 Agent LangGraph 状态

```ts
interface AgentWritingState {
  sessionId: string
  userInput: string
  approvalMode: AIApprovalMode
  approvalModeEffective: AIApprovalMode
  writingGoal: string
  userIntent?: string
  userPreferences?: Record<string, unknown>
  clarificationRequired: boolean
  clarificationQuestions: string[]
  clarificationAnswers: string[]
  categoryRegistry: CategoryRegistryItem[]
  existingPrefixes: Record<string, string[]>
  existingArticles: ArticleIndexItem[]
  draftPlan?: AIDraftPlan
  imagePlaceholders: string[]
  validationErrors: string[]
  riskFlags: string[]
  downgradeReasons: string[]
  reviewed: boolean
  confirmed: boolean
  createdPath?: string
  finalMarkdown?: string
}
```

### 8.3 Agent 节点

| 节点 | 职责 | 是否可写文件 |
| --- | --- | --- |
| `collect_context` | 读取分类注册表、文章列表、二级前缀、最近方案 | 否 |
| `parse_user_intent` | 识别用户目的、保留项、输入材料类型 | 否 |
| `clarify_intent` | 判断是否需要求证，最多生成 3 个问题 | 否 |
| `classify_input` | 确定写作目标和输入类型 | 否 |
| `plan_draft` | 调用 LLM 生成 `AIDraftPlan` | 否 |
| `validate_plan` | schema 和业务校验，风险降级 | 否 |
| `prepare_preview` | 生成预览路径、文件名、审核清单 | 否 |
| `wait_user_confirm` | 等待前端确认或修改方案 | 否 |
| `create_post` | 调用统一创建文章接口 | 是 |
| `write_markdown` | 调用统一更新文章接口 | 是 |
| `finish` | 返回结果和跳转信息 | 否 |

`plan` 接口只运行到 `prepare_preview`。

`commit` 接口从已确认的 `plan` 继续运行 `create_post`、`write_markdown`、`finish`。

### 8.4 LLM 模式编排

LLM 模式使用 LangChain 消息链即可，不需要完整 LangGraph。

流程：

1. 读取当前文章。
2. 构造作用范围上下文。
3. 调用 LLM 生成 `AIEditOperation`。
4. 校验 JSON 和操作可应用性。
5. 返回编辑预览。
6. 用户确认或权限允许时调用 apply 接口保存。

### 8.5 知识库模式编排

建议使用 LangGraph：

| 节点 | 职责 |
| --- | --- |
| `scan_or_load_index` | 读取缓存；缺失、过期、损坏时重建 |
| `classify_question` | 分类为 inventory、metadata、content、summary、unknown |
| `retrieve_evidence` | 检索文章、Front Matter、正文分块 |
| `validate_evidence` | 校验路径存在、hash 匹配、引用范围有效 |
| `answer_with_citations` | 基于证据生成回答 |
| `fallback` | 依据不足时输出未找到说明 |

清单统计类问题可以跳过 LLM，直接由扫描结果生成确定答案。

## 9. 提示词模板

### 9.1 通用系统提示词

```text
你是箓川码笺博客管理后台的 AI 写作助手。

你只能使用用户输入、当前文章内容、本地文章索引、分类注册表和系统明确提供的项目规则。
不得编造不存在的一级分类、二级前缀、文件路径、文章路径、接口能力、构建命令或项目配置。
不得声称你已经创建、保存、发布、删除、提交或修改文件；真实写入只能由后端接口完成。
必须区分“用户目的说明”和“文章正文素材”，不要把任务说明直接写进正文。
不确定时必须降低 confidence，并在 riskFlags、rationale 或 summary 中说明原因。
不得伪造或提升用户选择的 approvalMode。
遇到高风险、低置信度、求证未完成、图片占位不明确或作用范围不明确时，必须请求人工确认。
只能输出指定 JSON schema，不要输出 Markdown 代码块，不要输出解释文字。
```

### 9.2 Agent plan_draft 提示词

```text
任务：把用户输入整理为一份可继续编辑的博客草稿方案。

输入可能是杂乱笔记、一句话灵感、报错信息、代码片段、资料链接、文章大纲或用户对任务的说明。
如果用户说“整理这份笔记”“保留图片占位”“写成踩坑复盘”，这些是任务约束，不是正文内容。
是否保留图片占位只能从用户输入、原文图片语法、截图说明或“此处有图”等自然语言/内容线索中判断，不依赖单独的 UI 偏好字段。

规则：
1. 一级分类只能从 categoryRegistry 中选择。
2. prefix1 必须来自分类注册表。
3. prefix2 优先复用 existingPrefixes；无合适项时建议新的短前缀。
4. prefix2 不能为空，不能包含连字符。
5. title 是中文自然标题，不包含 prefix1、prefix2、.md。
6. bodyMarkdown 只包含正文 Markdown，不包含 Front Matter。
7. description 说明文章主题和读者收益，不能编造用户没有提供的事实。
8. 用户输入信息不足时，生成短草稿和待补充问题，不要虚构细节。
9. 图片、截图、附件只能保留占位，不得编造图片内容或路径。
10. 技术命令、API、版本、错误码、性能数据只能来自用户输入；否则标记待验证。
11. 个人经历、面试经历、项目经历不能新增用户没有提供的事实。

输出：严格符合 AIDraftPlan 的 JSON 对象。
```

### 9.3 LLM 编辑提示词

```text
任务：根据用户指令生成一条结构化文章编辑操作。

当前作用范围是 {scope}：
- selection：只能修改选中文本。
- cursor：只能生成插入内容。
- document：可以给出全文级修改方案，但不能直接保存。
- frontmatter：只能修改允许的 Front Matter 字段。

规则：
1. replace 必须包含 oldText 和 newText。
2. insert 必须包含 newText。
3. delete 必须包含 oldText 和 summary。
4. rewrite 必须包含完整 newText 和改动摘要。
5. frontmatter 必须包含 frontMatterPatch，不得混入正文。
6. 不明确或高风险时，requiresManualApproval 必须为 true。
7. 不得新增用户没有提供的事实、经历、数据或结论。
8. 用户要求发布、提交 Git、删除文件、部署或修改主题源码时，拒绝生成执行操作。

输出：严格符合 AIEditOperation 的 JSON 对象。
```

### 9.4 知识库问答提示词

```text
任务：基于系统提供的本地文章索引和正文分块回答用户问题。

你只能使用 evidence 中的文章、Front Matter、正文分块和引用来源。
不得使用模型记忆猜测用户写过哪些文章。
不得把通用知识当作用户文章中的内容。
找不到依据时，回答“当前文章中没有找到明确依据”。
回答具体内容问题时必须包含来源。
如果索引过期、扫描失败或引用校验失败，不得输出确定性结论。
```

## 10. Schema 校验

### 10.1 Agent 校验

校验分两层：Pydantic schema 校验和业务校验。

Pydantic 校验：

- JSON 可解析。
- 必填字段完整。
- 枚举合法。
- 数组字段类型正确。
- `confidence` 在 0 到 1。
- `clarificationQuestions` 最多 3 个。

业务校验：

- `primarySlug` 存在于分类注册表。
- `primaryName` 与注册表一致。
- `prefix1` 与注册表一致。
- `prefix2` 非空且不包含 `-`。
- `title` 非空。
- `description` 非空，建议 100 到 200 字；不足时给 warning，不一定阻断预览。
- `bodyMarkdown` 非空。
- `bodyMarkdown` 不包含 Front Matter 分隔符。
- `cover` 只能由系统根据分类注册表补齐。
- 高风险或低置信度时降级为请求批准。

### 10.2 LLM 编辑校验

- `type`、`scope`、`approvalMode` 在枚举范围内。
- `requiresManualApproval` 为布尔值。
- `replace.oldText` 必须能在作用范围内找到。
- `delete.oldText` 必须能在作用范围内找到。
- `insert.newText` 非空。
- `rewrite.newText` 非空，且不得包含非法 Front Matter。
- `frontMatterPatch` 只能修改白名单字段。
- 删除、全文重写、改一级分类默认需要人工确认。

### 10.3 知识库回答校验

- 引用路径必须存在。
- 引用标题必须与索引项一致。
- 引用分块 hash 必须与当前文章 hash 一致。
- 统计数量必须来自扫描结果。
- 回答中的文章标题不能超出检索结果范围。
- 具体内容回答至少包含一个来源。
- 依据不足时不能输出确定性结论。

### 10.4 JSON 修复重试

当 AI 返回非 JSON 或 schema 失败：

1. 后端尝试提取首个 JSON 对象。
2. 仍失败时，使用“格式修复提示词”最多重试一次。
3. 修复重试只能要求模型按原内容修复格式，不允许重新扩写。
4. 再失败则返回 `AI_JSON_INVALID`，不进入创建或写入流程。

## 11. 知识库索引缓存

### 11.1 缓存文件结构

`article-index.json`：

```json
{
  "schemaVersion": "1.0",
  "scannedAt": "2026-06-26T10:00:00+08:00",
  "root": "E:/A-Code/blog/blog-content/source",
  "articles": [],
  "failedFiles": [],
  "stats": {}
}
```

`article-chunks.json`：

```json
{
  "schemaVersion": "1.0",
  "scannedAt": "2026-06-26T10:00:00+08:00",
  "chunks": []
}
```

### 11.2 新鲜度判断

缓存视为过期的情况：

- 缓存文件不存在。
- JSON 解析失败。
- `schemaVersion` 不兼容。
- 任一文章文件的 mtime 晚于缓存扫描时间。
- 任一索引项的 `contentHash` 与当前文件不同。
- `_posts` 或 `_drafts` 中新增或删除 Markdown 文件。

### 11.3 重建策略

- 自动重建前先尝试读取旧缓存；旧缓存损坏则删除后重建。
- 重建写入使用临时文件，例如 `article-index.json.tmp`。
- 写入完成并验证 JSON 可读后再原子替换目标文件。
- 重建失败时保留旧缓存，但响应必须标记 `indexStatus: "failed"` 和 warning。

### 11.4 检索策略

第一阶段使用本地关键词检索：

- 标题精确匹配。
- 文件名匹配。
- 标签匹配。
- 分类匹配。
- description 匹配。
- 正文分块关键词匹配。

排序信号：

| 信号 | 权重 |
| --- | --- |
| 标题命中 | 高 |
| 标签命中 | 高 |
| 文件名命中 | 高 |
| 分类命中 | 中 |
| 小节标题命中 | 中 |
| 正文命中 | 低 |
| 最近更新时间 | 辅助 |

后续如需语义召回，可以增加本地 embedding 缓存文件，但不得引入独立向量数据库服务。embedding 也必须绑定 `contentHash`，并在回答前回到原文分块校验。

## 12. 异常处理

统一错误格式：

```json
{
  "success": false,
  "error": "用户可读错误信息",
  "data": {
    "code": "AI_JSON_INVALID",
    "recoverable": true,
    "sessionId": "uuid",
    "details": {}
  }
}
```

错误码建议：

| 错误码 | 场景 | 处理 |
| --- | --- | --- |
| `AI_MODEL_NOT_CONFIGURED` | 模型配置缺失 | 不发起 AI 请求，提示配置模型 |
| `AI_REQUEST_FAILED` | 模型调用失败 | 保留输入，允许重试 |
| `AI_JSON_INVALID` | AI 返回非 JSON | 最多修复重试一次，失败后阻断 |
| `AI_SCHEMA_INVALID` | schema 校验失败 | 返回校验错误，不创建文章 |
| `CATEGORY_INVALID` | 一级分类不在注册表 | 阻断创建，要求重选或重生成 |
| `PREFIX2_INVALID` | 二级前缀为空或包含 `-` | 阻断创建 |
| `RISK_REQUIRES_APPROVAL` | 风险与权限冲突 | 降级为请求批准 |
| `POST_CREATE_FAILED` | 创建文章失败 | 保留方案，允许修改标题或前缀重试 |
| `POST_WRITE_FAILED` | 创建后写入失败 | 返回已创建路径，允许重试写入 |
| `EDIT_CONFLICT` | 应用编辑时原文已变化 | 不自动覆盖，提示刷新 |
| `INDEX_SCAN_FAILED` | 索引扫描失败 | 返回已解析数量和失败文件 |
| `INDEX_STALE` | 索引过期 | 自动重建或提示重新扫描 |
| `EVIDENCE_NOT_FOUND` | 知识库依据不足 | 明确说明未找到依据 |
| `OUT_OF_SCOPE` | 用户要求越界操作 | 拒绝执行并说明边界 |

## 13. 安全边界

### 13.1 禁止自动执行

以下操作任何权限模式都不得由 AI 自动执行：

- 发布文章。
- 部署站点。
- 提交或推送 Git。
- 删除文章文件。
- 删除资源文件。
- 修改 `blog-content/themes/butterfly/`。
- 修改系统配置。
- 创建未注册一级分类。
- 执行任意命令行。
- 绕过后端接口直接写文件。

### 13.2 路径安全

所有来自前端或 AI 的路径必须经过规范化：

- 使用 `Path.resolve()` 得到绝对路径。
- 确认目标路径位于 `POSTS_DIR` 或允许的缓存目录内。
- 拒绝包含 `..`、绝对路径、盘符注入、URL schema 的路径。
- 知识库引用路径必须来自扫描索引，不接受 AI 自行生成路径。

### 13.3 内容安全

- 不把 API Key 写入日志。
- 不把完整模型配置回传前端，除非本来就是用户输入。
- 日志中可记录错误码、sessionId、路径、风险标记，不记录大段正文。
- 对可能包含敏感信息的输入打风险标记，不自动扩散或发布。

### 13.4 权限不可提升

- AI 输出中的 `approvalMode` 只能等于用户请求模式或被后端降级。
- AI 不能把 `request-approval` 改为 `full-access`。
- 前端传 `full-access` 也只在 AI 写作助手边界内有效。
- 后端最终以 `approvalModeEffective` 决定是否自动执行。

## 14. 日志与可追踪性

建议记录结构化日志：

```json
{
  "event": "ai_writing_plan_validated",
  "sessionId": "uuid",
  "approvalMode": "delegate-approval",
  "approvalModeEffective": "request-approval",
  "riskFlags": ["信息不足"],
  "validationErrorCount": 0,
  "createdPath": null
}
```

关键事件：

- AI 请求开始和结束。
- JSON 解析失败。
- schema 校验失败。
- 权限降级。
- 创建文章成功或失败。
- 写入文章成功或失败。
- 索引扫描开始、成功、失败。
- 知识库检索命中和依据不足。

## 15. 测试建议

### 15.1 单元测试

- 分类注册表生成。
- 文件名解析。
- Front Matter 解析和生成。
- Agent schema 校验。
- LLM 编辑操作校验。
- 权限降级规则。
- 索引新鲜度判断。
- Markdown 标题和分块提取。
- 知识库引用校验。

### 15.2 集成测试

- Agent 生成方案但不写文件。
- 请求批准模式下 commit 未确认时阻断。
- 替我审批低风险方案可创建草稿。
- 高风险方案自动降级。
- 创建成功后写入失败可恢复。
- LLM replace 操作在原文变化后返回冲突。
- 索引损坏后自动重建。
- 知识库清单问题不调用 LLM 生成事实。
- 具体内容问答包含来源。

### 15.3 手工验收场景

- 一句话灵感生成短草稿。
- Docker 报错笔记生成踩坑复盘。
- 粗糙学习笔记整理为技术研习文章。
- 要求保留图片占位时占位位置不丢失。
- 用户要求发布文章时 AI 拒绝越界执行。
- “我有哪些文章”返回本地扫描清单和数量。
- “我有没有写过 Hexo”返回匹配文章或未找到依据。

## 16. 实施顺序

推荐分阶段实现：

1. 新增分类注册表接口。
2. 抽取文章创建和更新服务，保证 AI 和普通编辑器复用同一写入能力。
3. 实现 Agent `plan` 接口、schema 和校验，不写文件。
4. 实现 Agent `commit` 接口、幂等和失败恢复。
5. 实现 LLM 编辑 `plan` 和 `apply`。
6. 实现本地文章扫描和索引缓存。
7. 实现知识库问答，先支持清单统计和元数据查询，再支持正文分块问答。
8. 补充日志、错误码、测试和前后端联调。

## 17. 开发注意事项

- AI 输出永远只是建议或结构化操作，真实写入必须经过后端业务校验。
- 创建文章和更新文章必须复用统一接口或同一底层服务。
- 不引入数据库；索引缓存必须可删除、可重建。
- 不要修改 `blog-content/themes/butterfly/`。
- 不要让知识库模式写入任何文章文件。
- 不要把模型通用知识伪装成用户文章已有内容。
- 任何失败都应返回可恢复状态，保留 `sessionId`、用户输入、草稿方案或已创建路径。
