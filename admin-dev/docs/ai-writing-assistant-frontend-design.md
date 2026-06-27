# AI 辅助写作前端技术文档

本文档根据 `admin-dev/docs/ai-writing-assistant-requirements.md` 编写，面向管理后台前端开发落地。目标是在现有 Vue 3 + TypeScript + Vite + Pinia + Naive UI + ByteMD 架构下，新增独立“AI 辅助写作”页面，并改造编辑器内 AI 写作侧边栏，使 Agent 模式、LLM 模式和知识库稳定模式具备一致的权限控制、校验、预览、错误处理和验收口径。

## 1. 前端目标

### 1.1 建设范围

- 新增独立页面：`/ai-writing`，菜单名为“AI 辅助写作”。
- 页面内提供三种手动切换模式：
  - Agent 模式：从想法、笔记、素材生成可创建的草稿方案。
  - LLM 模式：在页面内提供通用文章编辑对话入口；编辑器中保留并增强右侧 LLM 侧边栏。
  - 知识库稳定模式：基于本地文章索引和引用来源进行只读问答。
- 保留编辑器 `Editor.vue` 中的 AI 侧边栏入口，重构现有 `AIAssistant.vue` 为结构化编辑建议模式。
- 所有写入动作必须经过前端校验和后端接口校验，不能仅依赖 UI 权限。
- 前端不区分本地模式和在线模式，不直接拼接存储路径，不直接写文件。

### 1.2 非目标

- 不实现发布、部署、Git 提交、Git 推送、文件删除或主题源码修改能力。
- 不在前端引入长期数据库。
- 不绕过现有 `createPost`、`updatePost` 等统一 API。
- 不把 AI 返回内容直接视为可信事实；必须走 schema 校验、业务校验和风险降级。

## 2. 现有代码基础

当前前端关键结构：

```text
admin-dev/frontend/src/
├── App.vue
├── router.ts
├── api/
│   ├── index.ts
│   └── local.ts
├── components/
│   ├── AIAssistant.vue
│   └── NewPostModal.vue
├── stores/
│   ├── aiConfig.ts
│   ├── categories.ts
│   ├── posts.ts
│   └── settings.ts
├── types/
│   ├── api.ts
│   └── local.ts
└── views/
    ├── Dashboard.vue
    ├── Editor.vue
    ├── Media.vue
    ├── Posts.vue
    └── Settings.vue
```

建议新增：

```text
admin-dev/frontend/src/
├── views/
│   └── AIWriting.vue
├── components/ai-writing/
│   ├── ApprovalModeSelect.vue
│   ├── AIModelGuard.vue
│   ├── ModeSwitchTabs.vue
│   ├── AgentWorkspace.vue
│   ├── AgentInputPanel.vue
│   ├── AgentClarificationPanel.vue
│   ├── AgentPreviewPanel.vue
│   ├── AgentPlanMeta.vue
│   ├── AgentMarkdownPreview.vue
│   ├── LLMWorkspace.vue
│   ├── LLMChatPanel.vue
│   ├── LLMEditPreview.vue
│   ├── KnowledgeWorkspace.vue
│   ├── KnowledgeIndexPanel.vue
│   ├── KnowledgeAnswerPanel.vue
│   ├── RiskFlags.vue
│   ├── OperationLog.vue
│   └── ErrorState.vue
├── stores/
│   ├── aiWriting.ts
│   └── knowledgeIndex.ts
├── types/
│   └── ai-writing.ts
└── utils/
    ├── aiWritingValidation.ts
    ├── approvalPolicy.ts
    └── markdownPreview.ts
```

现有 `components/AIAssistant.vue` 可逐步拆为 `components/ai-writing/LLMSidebar.vue`，也可以先保留文件名，在内部接入新的类型、权限选择和结构化编辑预览。

## 3. 路由和菜单

### 3.1 路由

在 `src/router.ts` 新增：

```ts
{
  path: '/ai-writing',
  name: 'AIWriting',
  component: () => import('@/views/AIWriting.vue'),
  meta: { requiresAuth: true }
}
```

页面地址：

```text
http://localhost:14000/admin/#/ai-writing
```

### 3.2 侧边栏菜单

在 `App.vue` 的 `menuOptions` 中新增“AI 辅助写作”。位置建议放在“文章管理”和“编辑器”之间，表示它是创建与编辑的前置工作台。

菜单图标继续沿用当前 `renderMenuIcon` 方式，避免引入新图标库。

## 4. 页面整体结构

`AIWriting.vue` 负责页面级布局、模式切换和跨模式状态协调，不直接写复杂业务逻辑。

推荐布局：

```text
AIWriting.vue
├── 顶部栏
│   ├── 页面标题：AI 辅助写作
│   ├── 当前模型状态
│   └── 跳转设置按钮
├── 模式切换区
│   └── ModeSwitchTabs
├── 主内容区
│   ├── AgentWorkspace       mode = agent
│   ├── LLMWorkspace         mode = llm
│   └── KnowledgeWorkspace   mode = knowledge
└── 全局错误/日志区
    ├── ErrorState
    └── OperationLog
```

模式切换不销毁用户已输入内容，避免用户误切模式后丢失草稿。可用 `v-show` 保留组件实例，或将每个模式状态放入 Pinia。

## 5. 模式切换设计

### 5.1 模式枚举

```ts
export type AIWritingMode = 'agent' | 'llm' | 'knowledge'
```

UI 文案：

| 值 | 展示名 | 说明 |
| --- | --- | --- |
| `agent` | Agent 模式 | 从想法到草稿 |
| `llm` | LLM 模式 | 对文章内容进行编辑建议 |
| `knowledge` | 知识库稳定模式 | 基于本地文章问答 |

### 5.2 切换规则

- 用户必须手动切换模式，前端不根据输入自动跳转模式。
- 切换到 Agent 或 LLM 时展示权限选择，默认“请求批准”。
- 切换到知识库稳定模式时不展示写入权限选择，只展示只读状态。
- 生成中禁止切换模式，或切换前弹出确认“当前生成会被停止”。推荐第一期直接禁用切换。
- 切换模式不清空已输入内容、预览结果和历史记录。

### 5.3 顶层状态

```ts
interface AIWritingPageState {
  activeMode: AIWritingMode
  lastActiveAt: Record<AIWritingMode, number | null>
  globalError: AIWritingError | null
}
```

## 6. 权限选择 UI

### 6.1 权限枚举

```ts
export type AIApprovalMode =
  | 'request-approval'
  | 'delegate-approval'
  | 'full-access'
```

### 6.2 组件：`ApprovalModeSelect.vue`

使用位置：

- Agent 模式主输入框发送区。
- LLM 模式对话输入框发送区。
- 编辑器 AI 侧边栏输入区。

不在知识库稳定模式展示。

推荐 UI：

- 使用 `n-select` 或 `n-radio-group`，默认选中“请求批准”。
- 在选择控件旁展示一行短提示，说明授权只对当前消息或当前任务生效。
- 当实际执行被降级时，在控件下方展示 `n-alert`：
  - “已降级为请求批准：存在分类不确定/求证未完成/schema 校验失败。”

权限展示文案：

| 权限 | UI 文案 | 发送前提示 |
| --- | --- | --- |
| `request-approval` | 请求批准 | AI 只生成方案或建议，写入前需要你确认 |
| `delegate-approval` | 替我审批 | 低风险且校验通过时可自动采纳 |
| `full-access` | 完全访问权限 | 仅在当前 AI 写作任务内自动执行，不包含发布、Git、删除等系统操作 |

### 6.3 权限策略函数

放在 `utils/approvalPolicy.ts`：

```ts
interface ApprovalDecision {
  effectiveMode: AIApprovalMode
  requiresManualApproval: boolean
  downgraded: boolean
  reasons: string[]
}
```

输入包括：

- 用户选择的 `approvalMode`
- 操作类型
- schema 校验结果
- 风险标记
- 置信度
- 是否存在未回答求证问题
- 是否属于禁止能力

降级规则：

- schema 校验失败：降级并阻止写入。
- `riskFlags` 含高风险项：降级。
- `confidence < 0.7`：降级。
- `clarificationRequired = true` 且未确认继续：降级。
- 操作涉及发布、部署、Git、删除文件、主题源码、未注册一级分类：拒绝执行。

## 7. 类型定义

新增 `types/ai-writing.ts`。

### 7.1 Agent 草稿方案

```ts
export interface AIDraftPlan {
  schemaVersion: string
  approvalMode: AIApprovalMode
  writingGoal: WritingGoal
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

### 7.2 写作目标

```ts
export type WritingGoal =
  | 'auto'
  | 'blog-draft'
  | 'study-note'
  | 'pitfall-review'
  | 'project-log'
  | 'thought-essay'
  | 'resource-digest'
  | 'outline-expansion'
```

### 7.3 LLM 编辑操作

```ts
export type AIEditOperationType =
  | 'insert'
  | 'replace'
  | 'delete'
  | 'rewrite'
  | 'frontmatter'
  | 'clarify'
  | 'reject'

export type AIEditScope =
  | 'selection'
  | 'cursor'
  | 'document'
  | 'frontmatter'

export interface AIEditOperation {
  schemaVersion: string
  approvalMode: AIApprovalMode
  type: AIEditOperationType
  scope: AIEditScope
  summary: string
  oldText?: string
  newText?: string
  insertPosition?: number
  frontMatterPatch?: Partial<FrontMatter>
  riskFlags: string[]
  requiresManualApproval: boolean
  confidence: number
}
```

### 7.4 知识库问答

```ts
export interface KnowledgeCitation {
  title: string
  path: string
  heading?: string
  snippet?: string
}

export interface KnowledgeQAResponse {
  answer: string
  questionType: 'list' | 'stats' | 'lookup' | 'summary' | 'content' | 'unknown'
  scannedAt: string
  citations: KnowledgeCitation[]
  warnings: string[]
}
```

## 8. 状态管理

### 8.1 `useAIWritingStore`

负责独立写作页面和编辑器侧边栏共用的 AI 写作状态。

```ts
interface AIWritingStoreState {
  activeMode: AIWritingMode
  approvalMode: AIApprovalMode
  effectiveApprovalMode: AIApprovalMode
  isGenerating: boolean
  isCreatingDraft: boolean
  isApplyingEdit: boolean
  sessionId: string | null
  operationLog: AIOperationLogItem[]

  agent: AgentState
  llm: LLMState
}
```

Agent 状态：

```ts
interface AgentState {
  input: string
  writingGoal: WritingGoal
  audience: string
  expectedLength: string
  stylePreference: string
  saveAsInboxOnly: boolean
  clarificationAnswers: Record<string, string>
  continueWithCurrentUnderstanding: boolean
  plan: AIDraftPlan | null
  validation: ValidationResult | null
  createResultPath: string | null
  error: AIWritingError | null
}
```

LLM 状态：

```ts
interface LLMState {
  input: string
  chatHistory: AIChatMessage[]
  currentOperation: AIEditOperation | null
  validation: ValidationResult | null
  error: AIWritingError | null
}
```

### 8.2 `useKnowledgeIndexStore`

负责知识库稳定模式。

```ts
interface KnowledgeIndexState {
  indexStatus: 'unknown' | 'missing' | 'ready' | 'stale' | 'rebuilding' | 'error'
  scannedAt: string | null
  articleCount: number
  draftCount: number
  failedFiles: string[]
  isScanning: boolean
  isAsking: boolean
  question: string
  answer: KnowledgeQAResponse | null
  history: KnowledgeQAHistoryItem[]
  error: AIWritingError | null
}
```

### 8.3 与现有 store 的关系

- `settings.ts`：继续管理 AI 模型配置；页面通过 `activeModel` 判断是否可生成。
- `posts.ts`：创建草稿成功后调用 `addPostToCache` 或 `refreshPosts(true)`。
- `categories.ts`：如已有分类 store，应统一承载 `category-registry`；若现有实现不足，新增 action `fetchCategoryRegistry()`。

## 9. API 封装

在 `api/local.ts` 的 `LocalAPIClient` 中新增方法，类型同步到 `types/api.ts` 的 `BlogAPI`。

### 9.1 AI 对话

```ts
async aiChat(payload: AIChatRequest): Promise<AIChatResponse>
```

接口：

```http
POST /api/ai/chat
```

用途：

- Agent 模式生成结构化 `AIDraftPlan`。
- LLM 模式生成结构化 `AIEditOperation`。

请求必须包含：

- `mode`
- `approvalMode`
- `modelId` 或后端可识别的模型配置引用
- `messages` 或 `input`
- `context`
- `sessionId`

### 9.2 分类注册表

```ts
async getCategoryRegistry(): Promise<CategoryRegistryItem[]>
```

接口：

```http
GET /api/files/category-registry
```

前端用它校验：

- `primarySlug`
- `primaryName`
- `prefix1`
- `cover`

### 9.3 创建和更新文章

继续复用：

```ts
createPost('', '', { prefix1, prefix2, title })
updatePost(path, markdown)
```

Agent 创建草稿流程：

1. 调用 `createPost` 创建文件和基础 Front Matter。
2. 使用 AI 方案构建完整 Markdown。
3. 调用 `updatePost` 写入 Front Matter 和正文。
4. 成功后刷新 `posts` store。
5. 跳转编辑器：`/editor?file=${encodeURIComponent(path)}`。

### 9.4 文章索引

```ts
async scanArticleIndex(): Promise<ArticleIndexScanResult>
async getArticleIndex(): Promise<ArticleIndexSummary>
```

接口：

```http
POST /api/files/article-index/scan
GET /api/files/article-index
```

### 9.5 知识库问答

```ts
async knowledgeQA(payload: KnowledgeQARequest): Promise<KnowledgeQAResponse>
```

接口：

```http
POST /api/ai/knowledge-qa
```

此接口只读。前端不传任何写入授权，也不展示采纳、写入、创建按钮。

## 10. Agent 模式页面

### 10.1 页面结构

```text
AgentWorkspace
├── 左侧输入区
│   ├── AgentInputPanel
│   │   ├── 原始输入 textarea
│   │   ├── 素材上传 button/input
│   │   ├── 已添加素材状态条
│   │   ├── 先保存为待整理记录 checkbox/button
│   │   ├── ApprovalModeSelect
│   │   └── 生成草稿方案 button
│   └── AgentClarificationPanel
└── 右侧预览区
    ├── AgentPreviewPanel
    │   ├── AgentPlanMeta
    │   ├── RiskFlags
    │   ├── AgentMarkdownPreview
    │   ├── 审核清单
    │   └── 创建草稿操作区
    └── OperationLog
```

桌面端建议左右两栏：输入区 40%，预览区 60%。小屏可上下排列。

### 10.2 输入区字段

| 字段 | 类型 | 必填 | 默认值 |
| --- | --- | --- | --- |
| 原始输入 | textarea | 是 | 空 |
| 素材文件 | file input | 否 | 空 |
| 权限模式 | ApprovalModeSelect | 是 | 请求批准 |

写作目标、目标读者、期望篇幅、写作风格不提供独立手动表单。用户可以在原始输入中自然说明“写成踩坑复盘”“给刚入门的人看”“不要太长”“偏个人反思”等要求；前端统一发送 `writingGoal = auto`，由后端 Agent 根据输入和素材自动识别。

素材上传由输入框左下角加号触发。支持 `.md`、`.markdown`、`.txt`、`.text`、`.log`、`.docx` 文件；文本类素材可由前端直接读取，`.docx` 通过后端 `POST /api/ai/writing/material/extract` 提取正文段落。素材内容会以“附件素材”块追加到本次输入中，仅作为本次生成上下文，不会自动保存为博客文件。旧版 `.doc` 不做无依赖解析，前端提示用户另存为 `.docx`、`.md` 或 `.txt`。

图片占位不是独立表单项。用户从外部复制内容时，如果原文中包含 Markdown 图片语法、HTML 图片标签、截图说明、文件名或“此处有图”等线索，或者用户在输入中自然说明“保留图片位置占位”，前端只负责把这段原始输入原样发送给 Agent；是否保留、如何保留由后端 Agent 根据用户输入识别为写作约束。

发送前校验：

- 原始输入不能为空。
- 未配置 AI 模型时不发起请求，并展示跳转设置页入口。
- 输入很短也允许发送，但请求上下文标记 `lowInformationInput = true`。

### 10.3 求证面板

`AgentClarificationPanel` 展示 AI 输出的最多 3 个问题。

交互：

- 每个问题对应一个短文本输入框。
- 用户点击“带回答重新生成”后，将回答合并进下一次请求上下文。
- 用户点击“按当前理解继续”时：
  - 设置 `continueWithCurrentUnderstanding = true`。
  - 保留低置信度或风险提示。
  - 请求批准模式下仍需手动创建。

创建草稿禁用条件：

- `clarificationRequired = true`
- 用户没有回答问题
- 用户也没有选择“按当前理解继续”

### 10.4 Agent 预览页

`AgentPreviewPanel` 是 Agent 模式的核心审核界面。

必须展示：

- `sessionId`
- 权限模式和实际生效权限
- 写作目标
- AI 对用户目的的理解
- 输入类型
- 一级分类、一级前缀、二级前缀
- 标题
- 标签
- description
- 大纲
- 图片占位
- Markdown 正文预览
- 待补充问题
- 风险提示
- 置信度
- 分类和标题 rationale
- 创建前审核清单

可编辑字段：

- 一级分类：只能从分类注册表选择。
- 二级前缀：文本输入，禁止为空和 `-`。
- 标题：文本输入。
- 标签：标签编辑。
- description：textarea。
- 正文 Markdown：第一期可只预览；建议提供“复制到输入区继续改”或“编辑正文草稿”。

按钮状态：

| 按钮 | 出现条件 | 行为 |
| --- | --- | --- |
| 重新生成 | 有输入 | 重新请求 AI |
| 创建草稿 | 校验通过且需要人工确认 | 调用创建和更新流程 |
| 自动创建中 | 高权限且低风险 | 显示执行中状态 |
| 跳转编辑器 | 创建成功 | 跳转到新文章 |

### 10.5 Agent 校验

放在 `utils/aiWritingValidation.ts`。

校验项：

- JSON 可解析。
- `schemaVersion` 存在。
- `approvalMode` 合法。
- `writingGoal` 合法。
- `userIntent` 非空。
- `clarificationQuestions.length <= 3`。
- `primarySlug` 在分类注册表中。
- `primaryName` 与注册表一致。
- `prefix1` 与注册表一致。
- `prefix2` 非空且不含 `-`。
- `title` 非空。
- `description` 非空，建议 100 到 200 字；不满足时警告，创建前可允许用户确认，但不得静默通过。
- `bodyMarkdown` 非空。
- `bodyMarkdown` 不包含 Front Matter 分隔符。
- `confidence` 在 0 到 1。
- 数组字段必须为数组。

校验结果结构：

```ts
interface ValidationResult {
  valid: boolean
  blockingErrors: string[]
  warnings: string[]
}
```

### 10.6 Agent 创建草稿流程

```text
用户输入
  ↓
发送前校验
  ↓
POST /api/ai/chat 生成 AIDraftPlan
  ↓
JSON 解析 + schema 校验 + 分类校验 + 权限策略判断
  ↓
需要求证？
  ├─ 是：展示求证问题，不创建文章
  └─ 否：展示预览
        ↓
      是否允许自动创建？
        ├─ 否：等待用户点击“创建草稿”
        └─ 是：执行创建
              ↓
            POST /api/files/post
              ↓
            PUT /api/files/post/{path}
              ↓
            刷新文章缓存并跳转编辑器
```

重复点击防护：

- `isCreatingDraft = true` 时禁用创建按钮。
- 创建请求带当前 `sessionId` 和本地 `createRequestId`。
- 成功后锁定当前方案，避免同一方案重复创建。

## 11. LLM 模式与编辑器侧边栏

### 11.1 两个入口

LLM 能力有两个 UI 入口：

- 独立页面 `LLMWorkspace`：适合非特定文章的对话、草稿编辑建议或选择文章后编辑。
- 编辑器侧边栏 `AIAssistant.vue` / `LLMSidebar.vue`：基于当前打开文章、选区和光标执行结构化修改建议。

第一期必须优先保证编辑器侧边栏，因为它直接影响现有文章编辑体验。

### 11.2 编辑器侧边栏结构

```text
LLMSidebar
├── 折叠按钮
├── Drawer
│   ├── 当前作用范围提示
│   │   ├── 有选区：选区模式
│   │   ├── 无选区但有光标：光标插入模式
│   │   └── 用户要求全文：全文预览模式
│   ├── 快捷操作区
│   ├── ApprovalModeSelect
│   ├── 对话历史
│   ├── 生成中的响应
│   ├── LLMEditPreview
│   └── 输入区
└── 模型设置入口
```

现有 `AIAssistant.vue` 当前直接请求模型服务并返回纯文本，需改为：

- 优先调用后端 `POST /api/ai/chat`。
- 请求包含 `approvalMode`、`scope`、`selectedText`、`cursorPosition`、`frontMatter`、`bodyMarkdown`、`userInstruction`。
- AI 返回 `AIEditOperation`。
- 前端校验后再展示采纳、放弃或自动执行。

### 11.3 作用范围判断

```ts
function resolveEditScope(ctx: EditorContext, instruction: string): AIEditScope
```

规则：

- 有选中文本：默认 `selection`。
- 无选中且用户意图为插入/续写：`cursor`。
- 用户明确要求全文优化、重构、大纲调整：`document`。
- 用户明确要求改标题、描述、标签、分类：`frontmatter`。
- 范围不明确且操作有破坏性：返回 `clarify` 操作，不执行。

### 11.4 编辑预览

`LLMEditPreview.vue` 根据操作类型展示不同 UI：

| 操作 | 预览内容 | 采纳行为 |
| --- | --- | --- |
| `insert` | 插入位置、插入内容 | 插入到光标 |
| `replace` | old/new 对比 | 替换选区或匹配文本 |
| `delete` | 删除摘要和 oldText | 删除匹配内容 |
| `rewrite` | 全文预览和改动摘要 | 替换正文，保留 Front Matter |
| `frontmatter` | 字段 patch | 合并允许字段 |
| `clarify` | 澄清问题 | 不修改文章 |
| `reject` | 拒绝原因 | 不修改文章 |

`request-approval` 下所有操作都需要用户点击“采纳”。

`delegate-approval` 下可自动执行：

- 低风险 `insert`
- 低风险 `replace`
- 标题、description 等允许字段优化

必须手动确认：

- `delete`
- `rewrite`
- 分类前缀修改
- 风险标记非空
- `confidence < 0.7`

`full-access` 下可自动执行当前文章范围内的插入、替换、删除、全文重写和允许的 Front Matter 修改，但仍必须：

- 记录操作摘要。
- 保留撤销提示。
- 禁止发布、部署、Git、删除文件、主题源码修改。

### 11.5 编辑器应用函数

建议在 `Editor.vue` 中把现有 `handleInsertText` 拆成更明确的函数：

```ts
function applyInsert(newText: string, position: number): void
function applyReplace(oldText: string, newText: string, scope: AIEditScope): void
function applyDelete(oldText: string, scope: AIEditScope): void
function applyRewrite(newBodyMarkdown: string): void
function applyFrontMatterPatch(patch: Partial<FrontMatter>): void
```

校验要求：

- `replace.oldText` 必须能在作用范围内找到。
- `delete.oldText` 必须能在作用范围内找到。
- `rewrite` 只能替换正文，不丢 Front Matter。
- `frontmatter` 只能修改允许字段。

## 12. 知识库稳定模式页面

### 12.1 页面结构

```text
KnowledgeWorkspace
├── KnowledgeIndexPanel
│   ├── 索引状态
│   ├── 扫描时间
│   ├── 文章数量
│   ├── 草稿数量
│   ├── 失败文件
│   └── 重新扫描按钮
├── 问答区
│   ├── 问题输入框
│   ├── forceRescan checkbox
│   └── 发送按钮
└── KnowledgeAnswerPanel
    ├── 回答正文
    ├── 引用来源列表
    ├── warnings
    └── 历史记录
```

该模式必须明显标记“只读”。不展示 `ApprovalModeSelect`、创建、采纳、写入、保存按钮。

### 12.2 索引状态

| 状态 | 展示 | 可操作 |
| --- | --- | --- |
| `unknown` | 尚未加载索引 | 获取索引 |
| `missing` | 尚无索引 | 重新扫描 |
| `ready` | 索引可用 | 提问、重新扫描 |
| `stale` | 索引可能过期 | 建议重新扫描 |
| `rebuilding` | 正在重建 | 禁用提问 |
| `error` | 扫描失败 | 展示失败文件和重试 |

### 12.3 问答流程

```text
进入知识库稳定模式
  ↓
GET /api/files/article-index
  ↓
索引可用？
  ├─ 否：展示重新扫描
  └─ 是：允许提问
        ↓
      POST /api/ai/knowledge-qa
        ↓
      校验 citations 和 warnings
        ↓
      展示回答与来源
```

### 12.4 回答展示要求

- 清单统计类问题优先展示结构化列表或表格。
- 内容类问题必须展示引用来源。
- 找不到依据时展示空态：
  - “当前文章中没有找到明确依据。”
  - 显示检索关键词或主题。
- `warnings` 用 `n-alert` 展示，不能藏在日志里。
- 引用来源可点击时跳转编辑器：
  - `/editor?file=${encodeURIComponent(path)}`

## 13. 错误状态

统一错误类型：

```ts
interface AIWritingError {
  code: string
  title: string
  message: string
  details?: string
  retryable: boolean
  action?: {
    label: string
    handler: () => void
  }
}
```

### 13.1 错误码建议

| code | 场景 | 前端处理 |
| --- | --- | --- |
| `AI_MODEL_MISSING` | 未配置 AI 模型 | 提示跳转设置页，不发请求 |
| `AI_RESPONSE_NOT_JSON` | AI 返回非 JSON | 保留输入和历史，允许重新生成 |
| `SCHEMA_INVALID` | schema 校验失败 | 阻止写入，展示字段错误 |
| `CATEGORY_INVALID` | 分类不在注册表 | 阻止创建，允许手动选择 |
| `PREFIX2_INVALID` | 二级前缀非法 | 禁用创建按钮 |
| `RISK_DOWNGRADED` | 权限与风险冲突 | 降级请求批准，展示原因 |
| `OPERATION_FORBIDDEN` | 超出 AI 边界 | 拒绝执行，提示使用正式流程 |
| `CREATE_POST_FAILED` | 创建文章失败 | 保留方案，允许重试 |
| `UPDATE_POST_FAILED` | 写入正文失败 | 展示已创建路径，允许跳编辑器 |
| `INDEX_SCAN_FAILED` | 索引扫描失败 | 展示失败文件和重试 |
| `KNOWLEDGE_NO_EVIDENCE` | 知识库依据不足 | 明确无依据，不输出确定结论 |
| `NETWORK_ERROR` | 后端不可用 | 提示检查本地服务 |

### 13.2 错误 UI

`ErrorState.vue` 支持三种密度：

- inline：输入框下的小错误。
- panel：模式页面中的错误块。
- full：页面级不可继续错误。

所有错误都必须保留用户输入，不清空草稿方案。

## 14. 操作日志

`OperationLog.vue` 展示当前 session 的关键事件：

- 创建 session。
- 用户选择权限。
- AI 生成方案。
- 校验通过或失败。
- 权限降级原因。
- 用户回答求证问题。
- 创建文章请求开始/成功/失败。
- 更新文章请求开始/成功/失败。
- LLM 自动采纳或等待手动采纳。
- 知识库扫描和问答请求。

日志结构：

```ts
interface AIOperationLogItem {
  id: string
  time: string
  level: 'info' | 'success' | 'warning' | 'error'
  title: string
  detail?: string
}
```

日志只保存在当前前端会话中，第一期不要求持久化。

## 15. 前端校验和安全边界

### 15.1 禁止自动执行的能力

无论用户选择何种权限，前端都不能触发以下 AI 自动动作：

- 发布文章。
- 部署站点。
- Git commit。
- Git push。
- 删除文章文件。
- 删除资源文件。
- 修改 `themes/butterfly/`。
- 创建未注册一级分类。
- 修改系统配置。
- 执行命令行。

如果 AI 返回这些操作，前端应将其转换为 `OPERATION_FORBIDDEN`，并阻止执行。

### 15.2 Front Matter 允许字段

Agent 创建草稿允许设置：

- `title`
- `date`
- `updated`
- `categories`
- `tags`
- `description`
- `layout`
- `comments`
- `permalink`
- `excerpt`
- `published`
- `lang`
- `cover`
- `sticky`
- `slug`
- `status`
- `series`
- `series_order`

默认值要求：

- `layout: post`
- `comments: true`
- `published: true`
- `lang: zh-CN`
- `status: draft`
- `cover` 使用分类注册表中的 cover

LLM 修改 Front Matter 第一阶段建议只允许：

- `title`
- `tags`
- `description`
- `excerpt`
- `updated`

分类、封面、series 等字段需人工确认。

## 16. 开发步骤建议

### 16.1 第一阶段：页面骨架和类型

- 新增 `AIWriting.vue`。
- 新增路由和菜单。
- 新增 `types/ai-writing.ts`。
- 新增 `ApprovalModeSelect.vue`、`ModeSwitchTabs.vue`、`ErrorState.vue`。
- 新增 `useAIWritingStore`。

### 16.2 第二阶段：Agent 模式

- 实现 Agent 输入区。
- 接入 `POST /api/ai/chat`。
- 实现 JSON 解析和 schema 校验。
- 实现预览页。
- 接入 `createPost` 和 `updatePost`。
- 创建成功跳转编辑器。

### 16.3 第三阶段：编辑器 LLM 侧边栏

- 重构 `AIAssistant.vue` 请求后端统一 AI 接口。
- 增加权限选择。
- 增加结构化编辑操作预览。
- 拆分编辑器应用函数。
- 补齐自动采纳和降级规则。

### 16.4 第四阶段：知识库稳定模式

- 接入索引获取和扫描接口。
- 实现只读问答页。
- 展示引用来源和 warnings。
- 处理索引缺失、损坏、过期和扫描失败。

## 17. 验收点

### 17.1 基础页面

- 侧边栏出现“AI 辅助写作”菜单。
- `/ai-writing` 能正常打开。
- 页面可手动切换 Agent、LLM、知识库稳定模式。
- 切换模式不丢失已输入内容。
- 未配置模型时，Agent 和 LLM 不能发起生成，并提示去设置页。
- 知识库稳定模式不展示写入权限选择。

### 17.2 权限 UI

- Agent 和 LLM 发送前都能选择三种权限。
- 默认权限是“请求批准”。
- 权限只影响当前消息或当前任务。
- 风险、低置信度、求证未完成或 schema 失败时会自动降级。
- 完全访问权限也不能触发发布、Git、删除或主题源码修改。

### 17.3 Agent 模式

- 输入杂乱笔记能生成结构化草稿方案。
- 输入一句话想法时生成短草稿和待补充问题，不编造长文。
- AI 目的理解、写作目标、输入类型、分类、标题、标签、描述、大纲、正文预览都能展示。
- 求证问题最多 3 个。
- 求证未处理时不能创建草稿，除非用户选择按当前理解继续。
- 图片占位能在预览中展示。
- 分类必须来自注册表。
- 非法 `prefix2` 禁用创建。
- 请求批准模式下不自动创建文章。
- 替我审批和完全访问权限只在低风险且校验通过时自动创建。
- 创建草稿调用统一创建接口。
- 写入正文调用统一更新接口。
- 新文章状态为 `draft`。
- 创建成功后跳转编辑器。
- 创建失败不丢失草稿方案。
- 重复点击创建不会创建重复文章。

### 17.4 LLM 模式和侧边栏

- 编辑器侧边栏可以展开和收起。
- 侧边栏能读取当前文章、选区和光标位置。
- 有选区时默认只修改选区。
- 无选区时插入类操作插入到光标位置。
- 请求批准模式下必须点击采纳才修改文章。
- 删除操作展示删除摘要。
- 全文重写展示全文预览。
- Front Matter 修改展示字段 patch。
- 放弃后文章内容不变。
- 范围不明确的删除或全文修改不会直接执行。
- AI 不会把发布、提交、删除文件等请求转成可执行操作。

### 17.5 知识库稳定模式

- 进入模式后可看到索引状态。
- 索引缺失时可重新扫描。
- 扫描失败时展示失败文件。
- 用户问文章清单时返回本地扫描结果。
- 用户问文章数量时结果与索引一致。
- 用户问主题是否写过时返回匹配文章和依据。
- 内容类回答包含标题、路径和相关小节来源。
- 找不到依据时明确说明没有找到，不编造。
- 页面不提供任何写入、创建、采纳、保存按钮。

### 17.6 错误处理

- AI 返回非 JSON 时显示格式异常，并保留输入。
- schema 校验失败时阻止写入。
- 分类不可用时阻止创建并允许手动调整。
- 创建文章失败时展示后端错误并允许重试。
- 创建成功但写入失败时展示已创建路径并允许跳转编辑器。
- 网络错误时提示检查本地后端服务。
- 索引损坏或过期时提示重建，重建中不输出确定性知识库回答。

## 18. 测试建议

### 18.1 单元测试

优先覆盖：

- `validateDraftPlan`
- `validateEditOperation`
- `resolveApprovalDecision`
- `resolveEditScope`
- `buildMarkdown` 与 Front Matter 合并逻辑

### 18.2 组件测试

覆盖：

- `ApprovalModeSelect` 默认值和切换事件。
- `AgentPreviewPanel` 对风险、校验错误、按钮禁用状态的展示。
- `LLMEditPreview` 对不同操作类型的预览。
- `KnowledgeAnswerPanel` 对 citations 和 warnings 的展示。

### 18.3 手工验收用例

- 一句话灵感：`想写一篇关于 Codex 怎么帮我维护博客的短文`
- 踩坑笔记：粘贴报错、环境和解决过程。
- 图片占位：输入包含 `![截图](img1.png)` 和“此处有图”。
- 分类错误：模拟 AI 返回不存在的一级分类。
- LLM 选区润色：选中一段正文后请求润色。
- LLM 删除不明确：输入“删掉废话”，确认不会直接删除。
- 知识库清单：询问“我有哪些文章？”
- 知识库无依据：询问本地文章没有记录的主题。
