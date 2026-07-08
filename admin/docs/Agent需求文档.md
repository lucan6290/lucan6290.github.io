# 博客 AI Agent 需求文档

claude源码可参考：E:\A-Code\Claude-Code

## 1. 背景与目标

当前管理端已经有编辑器、文章管理、分类注册表、内容校验、构建任务等基础能力，也已经在前端出现了 AI 写作助手、Agent 运行协议、权限模式等雏形。下一步要补齐的是：让 AI 能在明确边界内辅助编辑文章、创建草稿、基于已有内容问答，同时保证所有读写都可审计、可回滚、可审批。

本功能不做一个万能 Agent，而是拆成三个垂直 Agent：

- 编辑器文章 Agent：只处理当前正在编辑的文章。
- 新文章创作 Agent：从想法、素材、笔记生成新文章。
- 知识库问答 Agent：只读已有文章，基于证据回答问题。

核心目标：

- 所有文件读写都经过后端工具，不允许模型直接操作文件系统。
- Agent 只负责理解意图、生成结构化计划和解释结果。
- 后端作为安全边界，负责路径校验、权限判断、hash 校验、schema 校验、diff 预览、写入和审批恢复。
- 前端使用统一事件流展示 Agent 执行过程，减少三套 UI 和三套状态机。

## 2. 总体架构

建议分为五层：

```text
前端 Agent UI
-> Agent Run API
-> Agent Orchestrator
-> ToolRuntime / PolicyEngine / ApprovalStore / SessionStore
-> 现有文章、分类、索引、校验、写入服务
```

### 2.1 Agent Orchestrator

Agent Orchestrator 负责调度单次 Agent 运行：

- 识别 `agentType` 和 `command`。
- 加载 session。
- 调用 LLM 生成结构化计划。
- 调用后端工具读取、预览、校验、写入。
- 生成统一事件 `events`。
- 在需要用户确认时返回 `waiting_approval`。

### 2.2 ToolRuntime

ToolRuntime 是唯一允许执行实际操作的层。模型不能直接调用文件系统、命令行、Git、部署或任意网络请求。

工具分为：

- 文章工具：读文章、预览 diff、写文章、创建文章、校验 schema。
- 分类工具：读取分类注册表、校验分类路径。
- 索引工具：扫描文章、检索文章块。
- 网页工具：安全抓取用户显式提供的 URL。
- 审批工具：保存 approval、resume 后继续执行。

### 2.3 PolicyEngine

PolicyEngine 统一判断权限模式和风险等级：

- `request-approval`：任何写入必须确认。
- `delegate-approval`：低风险操作可自动执行，高风险操作必须确认。
- `full-access`：可自动执行，但仍必须通过路径、hash、schema、风险边界校验。

风险判断不要散落在各个 Agent 中，应由后端统一实现。

### 2.4 SessionStore 与 ApprovalStore

SessionStore 保存 Agent 运行上下文。ApprovalStore 保存待审批动作，至少包含：

- `sessionId`
- `approvalId`
- `agentType`
- `command`
- `operation`
- `payloadHash`
- `expectedContentHash`
- `target`
- `riskFlags`
- `createdAt`
- `expiresAt`

用户确认后通过 resume 接口继续执行，前端不应重新拼装敏感写入参数。

### 2.5 LLM Adapter

LLM Adapter 由后端统一管理模型配置和模型调用。前端不直接传 API Key、Base URL、完整模型参数，也不直接请求第三方模型接口。

- 前端只传 `modelConfigId` 或后端认可的 `modelId`。
- 后端保存和读取 API Key、Base URL、模型 ID、供应商、兼容协议、temperature、max tokens、thinking/reasoning 等参数。
- 后端统一处理 OpenAI-compatible、Anthropic-compatible、DeepSeek thinking/reasoning 等模型差异。
- 后端负责模型调用日志、错误归一化、超时、重试、限流和敏感信息脱敏。
- 前端只展示可选模型、当前模型、调用状态和错误提示。

这样可以减少 API Key 暴露面，也方便审计和限流。

## 3. 统一 Agent 运行协议

三个 Agent 使用统一请求和响应结构。

### 3.1 请求结构

```ts
interface AgentRunRequest {
  sessionId?: string
  agentType: 'editor' | 'writing' | 'knowledge'
  command: string
  userInput?: string
  approvalMode: 'request-approval' | 'delegate-approval' | 'full-access'
  confirmed?: boolean
  context?: Record<string, unknown>
  model?: AIModelPayload
  articlePath?: string
  selection?: EditorSelection
  operation?: unknown
  plan?: unknown
  expectedContentHash?: string
}
```

### 3.2 响应结构

```ts
interface AgentRunResponse<T = unknown> {
  sessionId: string
  agentType: 'editor' | 'writing' | 'knowledge'
  status: 'completed' | 'failed' | 'waiting_approval'
  events: AgentEvent[]
  result?: T
}
```

### 3.3 事件结构

```ts
type AgentEventType =
  | 'session'
  | 'message'
  | 'tool_call'
  | 'tool_result'
  | 'approval_required'
  | 'error'
  | 'done'

interface AgentEvent {
  type: AgentEventType
  message: string
  data?: unknown
  toolCallId?: string
}
```

第一版先返回完整 `events[]`，不强制做 SSE。等核心流程稳定后，再增加流式事件接口。

## 4. Agent 一：编辑器文章 Agent

### 4.1 作用

辅助修改当前正在编辑的文章。它只能操作当前绑定文章，不能切换目标文章，不能创建新文章，不能发布、部署、提交 Git。

### 4.2 能力

- `read_current_article`
- `get_current_selection`
- `plan_current_article_edit`
- `preview_current_article_edit`
- `write_current_article`
- `approval_resume`

可选工具：

- `web_search`
- `fetch_web_source`
- `summarize_web_source`
- `attach_source_citation`

联网工具分为 Web Search 和 URL Fetch 两类：

- 当用户明确提出“搜索”“查一下”“最新版本”“联网确认”等需求时，Agent 可以使用受控 Web Search 工具检索公开网页，并基于搜索结果回答或补充编辑方案。
- 当需要抓取、解析、引用某个具体网页正文时，必须通过受控 URL Fetch 工具，并满足网页安全策略。
- Agent 不允许脱离用户意图自行联网，也不允许把 Web Search / URL Fetch 当成通用浏览器代理。

### 4.3 编辑操作结构

```ts
interface EditorAgentOperation {
  type: 'insert' | 'replace' | 'delete' | 'rewrite' | 'frontmatter'
  scope: 'document' | 'selection' | 'frontmatter'
  summary: string
  oldText?: string
  newText?: string
  insertPosition?: 'append' | 'prepend' | 'before_old_text' | 'after_old_text'
  frontMatterPatch?: Record<string, unknown>
  riskFlags: string[]
  confidence: number
}
```

选区建议包含文本和位置：

```ts
interface EditorSelection {
  text: string
  startOffset?: number
  endOffset?: number
  startLine?: number
  endLine?: number
}
```

### 4.4 必须校验

写入前必须校验：

- `articlePath` 属于当前允许的文章目录。
- `articlePath` 与 session 绑定的文章一致。
- `expectedContentHash` 与当前文件 hash 一致。
- front matter 和正文满足 schema。
- 操作风险等级与权限模式匹配。
- `oldText` 匹配当前文章内容，避免替换错位置。

### 4.5 风险等级

低风险：

- 追加一小段内容。
- 替换当前选区。
- 局部润色。
- 补充说明。

中风险：

- 多段落重写。
- 插入来源引用。
- 修改标题或描述。

高风险：

- 删除内容。
- 全文重写。
- 修改 front matter。
- 修改分类、标签、发布时间、草稿状态。
- 大范围结构调整。

阻断：

- 路径越界。
- 试图写入非当前文章。
- hash 冲突。
- schema 不合法。
- 操作目标无法定位。

### 4.6 典型流程

```text
用户输入编辑指令
-> Agent 读取当前文章和选区
-> LLM 生成 EditorAgentOperation
-> ToolRuntime 生成 diff、riskFlags、beforeHash
-> 前端展示 diff、riskFlags、validationErrors
-> 用户点击采纳
-> ToolRuntime 校验 hash、路径、schema、权限
-> 可自动写入则写入
-> 需要确认则返回 waiting_approval
-> 用户确认后 resume
-> 返回 saved result、latestContentHash、indexSyncStatus
```

## 5. Agent 二：新文章创作 Agent

### 5.1 作用

从用户想法、素材、笔记中生成一篇新博客或文档草稿。它负责生成草稿方案，用户确认后创建文章。

### 5.2 能力

- `read_blog_rules`
- `get_category_registry`
- `list_existing_posts`
- `plan_draft`
- `create_post`
- `write_created_post`

### 5.3 关键边界

- 只复用后端已有 create / update 能力。
- 不直接运行 Docusaurus、构建、发布、部署、Git 命令。
- 第一版不自动新增分类，只能建议新增分类。
- 只能写入本 session 创建的文章。
- 创建文章在 `request-approval` 和 `delegate-approval` 下都建议要求确认。
- 创建成功后返回编辑器跳转地址，由用户继续编辑。

### 5.4 草稿计划结构

```ts
interface AIDraftPlan {
  schemaVersion: string
  approvalMode: 'request-approval' | 'delegate-approval' | 'full-access'
  writingGoal: string
  userIntent: string
  title: string
  type: 'docs' | 'blog'
  primarySlug: string
  primaryName: string
  prefix1: string
  prefix2?: string
  tags: string[]
  description: string
  outline: string[]
  bodyMarkdown: string
  imagePlaceholders: string[]
  missingInfoQuestions: string[]
  riskFlags: string[]
  confidence: number
  reviewChecklist: string[]
  rationale: string
}
```

### 5.5 典型流程

```text
用户输入写作想法
-> Agent 读取写作规则
-> Agent 读取分类注册表
-> Agent 读取已有文章列表，检查重复和命名冲突
-> LLM 生成 AIDraftPlan
-> 前端展示标题、分类、标签、描述、大纲、正文预览、风险提示
-> 用户确认创建
-> 后端 create_post 创建文章
-> 后端 write_created_post 写入 front matter 和正文
-> 返回 path、editorUrl、latestContentHash、indexSyncStatus
```

## 6. Agent 三：知识库问答 Agent

### 6.1 作用

基于博客已有文章回答问题。该 Agent 只读不写，不创建文章，不修改索引以外的内容，不发布、不部署、不提交 Git。

### 6.2 能力

- `scan_article_index(force)`
- `search_article_chunks(query)`
- `answer_with_citations(question, evidence)`

### 6.3 回答约束

- 回答必须基于 evidence。
- 回答必须带 citations。
- 没有证据时明确返回“当前文章中没有找到明确依据”。
- 不允许模型脱离 evidence 编造事实。
- 引用应包含标题、路径、标题层级、行号或片段。

### 6.4 引用结构

```ts
interface KnowledgeCitation {
  title: string
  path: string
  heading?: string
  headingPath?: string[]
  lines?: number[]
  snippet?: string
}
```

### 6.5 典型流程

```text
用户提问
-> 复用现有索引或强制重建索引
-> search_article_chunks 检索 evidence
-> 无 evidence：明确回答不知道
-> 有 evidence：基于 evidence 生成 answer
-> 返回 answer、citations、warnings
```

## 7. 共享工具：网页检索与导入

网页检索与导入不是独立 Agent，而是编辑器文章 Agent 和新文章创作 Agent 的共享工具。它包含两类能力：

- Web Search：当用户明确要求搜索、查最新资料、确认外部事实时，Agent 可以检索公开网页。
- URL Fetch：当用户提供 URL，或 Web Search 返回结果经后端筛选后需要抓取正文时，后端可以抓取并提取网页内容。

### 7.1 能力

- `web_search(query, limit)`
- `fetch_url(url)`
- `extract_web_article(fetchResultId)`
- `summarize_web_source(sourceId, purpose)`
- `attach_source_citation(postPath, sourceId)`

### 7.2 安全要求

网页检索和网页抓取必须由后端执行，不能由模型或前端直接访问第三方网页。

Web Search 触发条件：

- 用户明确提出搜索、查找、联网确认、最新资料、当前版本等需求。
- 用户确认需要补充外部来源。
- Agent 在生成方案时发现缺少外部事实依据，但必须先在事件中说明将执行 Web Search。

Web Search 限制：

- 只能使用后端配置的搜索供应商或搜索工具。
- 搜索 query 必须来自用户问题或当前任务上下文，不能由模型任意扩展成不相关查询。
- 搜索结果必须保留来源标题、URL、摘要和检索时间。
- 基于搜索结果回答时必须附来源；没有可靠来源时必须明确说明不确定。

URL Fetch 限制：

- 用户显式提供 URL 时可以抓取。
- Web Search 返回的候选 URL 经后端安全校验后可以抓取。
- 抓取正文后必须保存 sourceId，便于摘要、引用和审计。

必须限制：

- 只允许 `http` 和 `https`。
- 禁止 userinfo URL。
- 禁止 localhost、127.0.0.1、0.0.0.0。
- 禁止内网 IP、回环地址、链路本地地址、云元数据地址。
- 限制重定向次数。
- 限制响应大小。
- 限制超时时间。
- 不携带 cookie。
- 不读取登录态。
- 不做通用浏览器代理。
- 不允许模型绕过 Web Search / URL Fetch 工具自主访问网络。

## 8. 后端 API 建议

建议新增统一 Agent 路由：

```text
POST /api/v1/agents/editor/runs
POST /api/v1/agents/writing/runs
POST /api/v1/agents/knowledge/runs
POST /api/v1/agent-approvals/{approval_id}/resume
```

网页工具可以独立为受控资源：

```text
POST /api/v1/web-sources/fetch
POST /api/v1/web-sources/{source_id}/summarize
POST /api/v1/articles/{article_id}/sources
```

第一版也可以只实现：

```text
POST /api/v1/agents/editor/runs
POST /api/v1/agent-approvals/{approval_id}/resume
```

等编辑器闭环稳定后，再扩展 writing、knowledge 和 web-sources。

## 9. 前端界面需求

### 9.1 编辑器侧边栏

需要展示：

- 用户输入框。
- 权限模式选择。
- 当前模型选择。
- Agent 事件流。
- diff 预览。
- `riskFlags`。
- `validationErrors`。
- `approval_required` 状态。
- 采纳、确认、取消。
- 写入成功提示。
- hash 冲突提示。

### 9.2 AI 辅助写作页面

需要展示：

- 用户想法输入。
- 素材输入或上传。
- 草稿方案。
- 分类建议。
- 标题、标签、描述、大纲、正文预览。
- 风险提示。
- 确认创建。
- 创建成功后的编辑器跳转链接。

### 9.3 知识库入口

需要展示：

- 问题输入。
- 是否强制重建索引。
- 回答内容。
- 引用列表。
- 无证据提示。
- Agent 检索事件。

## 10. 最小可行版本路线

第一阶段只做编辑器文章 Agent，先跑通“当前文章可控编辑”：

1. 定义后端 Agent DTO、事件 DTO、approval DTO。
2. 新增 `/api/v1/agents/editor/runs` 路由骨架。
3. 实现 `read_current_article`。
4. 实现 `plan_current_article_edit`，要求 LLM 输出结构化 `EditorAgentOperation`。
5. 实现 `preview_current_article_edit`，返回 diff、riskFlags、beforeHash、validationErrors。
6. 实现 `write_current_article`，强制校验路径、当前文章、hash、schema、权限。
7. 实现 `request-approval` 和 `delegate-approval`。
8. 实现 `approval resume`。
9. 前端 `localAPI.runEditorAgent` 接入后端。
10. 编辑器侧边栏跑通输入指令、预览 diff、采纳写入、审批恢复。

第二阶段做新文章创作 Agent：

1. 读取写作规范、分类注册表、已有文章。
2. 生成 `AIDraftPlan`。
3. 用户确认后创建文章。
4. 返回编辑器跳转地址。

第三阶段做知识库问答 Agent：

1. 复用或新增文章索引。
2. 检索文章块。
3. 基于 evidence 回答。
4. 展示 citations。

第四阶段做网页导入工具：

1. 实现 SSRF 防护。
2. 实现抓取、正文提取、摘要和引用附加。
3. 接入编辑器 Agent 和新文章创作 Agent。

第五阶段增强体验：

1. SSE 事件流。
2. session 持久化。
3. 模型配置后端化。
4. 更细的审计日志。
5. 更完整的测试和接口文档。

## 11. 验收标准

功能验收：

- 三个 Agent 职责清晰，没有万能 Agent。
- 编辑器 Agent 只能写当前绑定文章。
- 新文章 Agent 只能写自己本轮创建的文章。
- 知识库 Agent 只读不写。
- 前端可以展示完整 Agent 事件。
- 前端可以展示 diff、风险、校验错误和审批状态。
- 创建草稿后可以跳转编辑器继续编辑。
- 知识库回答包含 citations。

安全验收：

- 所有写入都经过后端工具。
- 所有写入都有 hash 校验。
- 高风险操作会触发审批。
- 路径越界会被阻断。
- schema 不合法会被阻断。
- 网页抓取有 SSRF 防护。
- 不执行 Git commit、push、deploy。
- 不运行任意 shell。
- 不让模型直接操作文件系统。
- 不允许模型任意访问网络。

工程验收：

- Agent 请求和响应协议统一。
- 权限模式由后端统一判断。
- Approval 可以 resume。
- 失败响应包含可展示的错误信息。
- 测试覆盖低风险写入、高风险审批、hash 冲突、路径越界、schema 错误、无证据问答。

## 12. 当前项目落地提示

当前前端已经存在部分 Agent 类型和 UI 雏形：

- `admin/frontend/src/types/ai-writing.ts` 已定义 `AgentRunResponse`、`AgentEvent`、`EditorAgentRunRequest`。
- `admin/frontend/src/components/AIAssistant.vue` 已经按 `runEditorAgent` 的方式调用编辑器 Agent。
- `admin/frontend/src/api/local.ts` 预留了 `/ai/draft`、`/ai/rewrite`。

当前后端还没有对应的 `ai` 或 `agents` 路由。建议优先补后端 Agent 路由和 `localAPI.runEditorAgent`，让编辑器弹出的 AI 辅助框先形成完整闭环。

## 13. 与现有内容工作流的关系

Agent 功能不是重做文章系统，而是在现有内容工作流之上增加一层智能编排。

现有能力应继续作为底座复用：

- 文章读取、创建、更新、移动、删除。
- front matter 解析和写入。
- 文章 schema 校验。
- 分类、标签、注册表同步。
- sidebar / blog index / registry index 同步。
- 图片管理和引用校验。

Agent 新增的是：

- 后端模型配置管理。
- `LLMAdapter` 模型调用层。
- Agent Orchestrator 编排层。
- ToolRuntime 工具执行层。
- PolicyEngine 权限和风险判断。
- SessionStore / ApprovalStore 审批恢复。
- Agent 专用 prompt 和结构化输出解析。

典型调用关系：

```text
EditorAgent
-> 复用 ArticleService 读取当前文章
-> LLMAdapter 生成 EditorAgentOperation
-> ToolRuntime 生成 diff 和风险标记
-> 复用现有校验服务校验 schema / 路径 / hash
-> 复用现有保存服务写入文章
-> 复用索引同步服务更新 registry index
```

新文章创作 Agent 也应复用现有 create article workflow，而不是绕过工作流直接写文件。

模型配置与文章工作流是两条不同能力线：

- 模型配置解决“用哪个模型、如何调用模型、密钥在哪里保存”。
- 文章工作流解决“文章如何被创建、校验、写入和同步”。

Agent 运行时把两者连接起来，但不能替代现有内容工作流。
