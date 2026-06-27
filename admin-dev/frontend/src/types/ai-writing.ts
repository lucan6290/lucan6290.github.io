import type { FrontMatter } from '@/types/api'

export type AIWritingMode = 'agent' | 'llm' | 'knowledge'

export type AIApprovalMode =
  | 'request-approval'
  | 'delegate-approval'
  | 'full-access'

export type WritingGoal =
  | 'auto'
  | 'blog-draft'
  | 'study-note'
  | 'pitfall-review'
  | 'project-log'
  | 'thought-essay'
  | 'resource-digest'
  | 'outline-expansion'

export interface CategoryRegistryItem {
  frontend_name1: string
  category_slug: string
  note_prefix1: string
  cover: string
  sort_order: number
  enabled: boolean
  children: CategoryRegistryChild[]
  prefix1: string
  primaryName: string
  primarySlug: string
  dir: string
}

export interface CategoryRegistryChild {
  frontend_name2: string
  note_prefix2: string
  sort_order: number
  enabled: boolean
}

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
  schemaVersion?: string
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

export interface EditPlanRequest {
  sessionId?: string
  articlePath: string
  instruction: string
  approvalMode: AIApprovalMode
  scope: AIEditScope
  selection?: {
    text: string
    startLine?: number
    endLine?: number
  }
  model: AIModelPayload
}

export interface EditPlanResponse {
  sessionId: string
  operation: AIEditOperation | null
  validationErrors: string[]
  warnings: string[]
}

export interface EditApplyRequest {
  sessionId: string
  articlePath: string
  approvalMode: AIApprovalMode
  confirmed: boolean
  operation: AIEditOperation
}

export interface AIChatMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export interface AIChatRequest {
  mode: 'agent' | 'llm'
  approvalMode: AIApprovalMode
  sessionId: string
  input: string
  context?: Record<string, unknown>
  messages?: AIChatMessage[]
}

export interface AIChatResponse<T = unknown> {
  sessionId?: string
  content?: string
  data?: T
  warnings?: string[]
}

export interface AIModelPayload {
  baseUrl: string
  apiKey: string
  modelId: string
  provider?: string
  apiFormat?: 'openai' | 'anthropic'
  anthropicBaseUrl?: string
  thinkingMode?: 'enabled' | 'disabled'
  reasoningEffort?: 'high' | 'max'
  agentMode?: boolean
  toolCalls?: boolean
  strictToolCalls?: boolean
  jsonMode?: boolean
  temperature?: number
  maxTokens?: number
}

export interface AgentPlanRequest {
  sessionId?: string
  userInput: string
  approvalMode: AIApprovalMode
  writingGoal: WritingGoal
  userPreferences: Record<string, unknown>
  clarificationAnswers: string[]
  conversationHistory?: AIChatMessage[]
  model: AIModelPayload
}

export interface AgentPlanResponse {
  sessionId: string
  plan: AIDraftPlan | null
  preview: {
    requiresManualApproval?: boolean
    approvalModeEffective?: AIApprovalMode
    downgradeReasons?: string[]
    [key: string]: unknown
  } | null
  validationErrors: string[]
  warnings: string[]
}

export interface AgentCommitRequest {
  sessionId: string
  approvalMode: AIApprovalMode
  confirmed: boolean
  idempotencyKey: string
  plan: AIDraftPlan
}

export interface AgentCommitResponse {
  path: string
  created: boolean
  written: boolean
  editorUrl?: string
  warnings: string[]
  unusedImages?: unknown[]
}

export interface WritingMaterialExtractResponse {
  filename: string
  content: string
  contentType: string
  warnings: string[]
}

export interface ArticleIndexScanResult {
  scannedAt: string
  articleCount: number
  draftCount: number
  indexStatus: 'rebuilt' | 'ready' | 'fresh' | 'partial' | 'failed'
  failedFiles: string[]
  stats?: Record<string, unknown>
}

export interface ArticleIndexSummary extends ArticleIndexScanResult {
  articles?: unknown[]
  categoryStats?: Record<string, number>
  tagStats?: Record<string, number>
  statusStats?: Record<string, number>
  warnings?: string[]
}

export interface KnowledgeCitation {
  title: string
  path: string
  heading?: string
  headingPath?: string[]
  lines?: number[]
  snippet?: string
}

export interface KnowledgeQARequest {
  sessionId?: string
  question: string
  forceRescan: boolean
  includeDrafts?: boolean
  model?: AIModelPayload
}

export interface KnowledgeQAResponse {
  answer: string
  questionType: 'inventory' | 'metadata' | 'summary' | 'content' | 'list' | 'stats' | 'lookup' | 'unknown'
  scannedAt: string
  citations: KnowledgeCitation[]
  warnings: string[]
}

export interface ValidationResult {
  valid: boolean
  blockingErrors: string[]
  warnings: string[]
}

export interface AIWritingError {
  code: string
  title: string
  message: string
  details?: string
  retryable: boolean
}

export interface AIOperationLogItem {
  id: string
  time: string
  level: 'info' | 'success' | 'warning' | 'error'
  title: string
  detail?: string
}

export interface ApprovalDecision {
  effectiveMode: AIApprovalMode
  requiresManualApproval: boolean
  downgraded: boolean
  blocked: boolean
  reasons: string[]
}
