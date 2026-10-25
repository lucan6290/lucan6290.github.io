import type {
  AIApprovalMode,
  AIDraftPlan,
  AIEditOperation,
  CategoryRegistryItem,
  ValidationResult
} from '@/types/ai-writing'

const APPROVAL_MODES: AIApprovalMode[] = [
  'request-approval',
  'delegate-approval',
  'full-access'
]

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every(item => typeof item === 'string')
}

export function parseJSONPayload<T>(payload: unknown): T {
  if (typeof payload !== 'string') {
    return payload as T
  }

  const trimmed = payload.trim()
  const fencedMatch = trimmed.match(/^```(?:json)?\s*([\s\S]*?)\s*```$/)
  return JSON.parse(fencedMatch ? fencedMatch[1] : trimmed) as T
}

export function validateDraftPlan(
  value: unknown,
  registry: CategoryRegistryItem[]
): ValidationResult {
  const blockingErrors: string[] = []
  const warnings: string[] = []

  if (!isRecord(value)) {
    return {
      valid: false,
      blockingErrors: ['AI 返回内容不是有效对象'],
      warnings
    }
  }

  const plan = value as Partial<AIDraftPlan>

  if (!plan.schemaVersion) blockingErrors.push('缺少 schemaVersion')
  if (!plan.userIntent) blockingErrors.push('缺少用户目的理解')
  if (!plan.title) blockingErrors.push('标题不能为空')
  if (!plan.description) blockingErrors.push('文章描述不能为空')
  if (!plan.bodyMarkdown) blockingErrors.push('正文不能为空')

  if (!plan.approvalMode || !APPROVAL_MODES.includes(plan.approvalMode)) {
    blockingErrors.push('权限模式不合法')
  }

  if (!plan.writingGoal || typeof plan.writingGoal !== 'string') {
    blockingErrors.push('写作目标不合法')
  }

  if (typeof plan.clarificationRequired !== 'boolean') {
    blockingErrors.push('clarificationRequired 必须是布尔值')
  }

  if (!isStringArray(plan.clarificationQuestions)) {
    blockingErrors.push('clarificationQuestions 必须是字符串数组')
  } else if (plan.clarificationQuestions.length > 3) {
    blockingErrors.push('求证问题不能超过 3 个')
  }

  if (!plan.prefix2) {
    blockingErrors.push('二级前缀不能为空')
  } else if (plan.prefix2.includes('-')) {
    blockingErrors.push('二级前缀不能包含连字符')
  }

  const category = registry.find(item => item.primarySlug === plan.primarySlug)
  if (!category) {
    blockingErrors.push('一级分类不在注册表中')
  } else {
    if (plan.primaryName !== category.primaryName) {
      blockingErrors.push('一级分类中文名与注册表不一致')
    }
    if (plan.prefix1 !== category.prefix1) {
      blockingErrors.push('一级分类前缀与注册表不一致')
    }
  }

  if (typeof plan.confidence !== 'number' || plan.confidence < 0 || plan.confidence > 1) {
    blockingErrors.push('confidence 必须是 0 到 1 之间的数字')
  } else if (plan.confidence < 0.7) {
    warnings.push('置信度低于 0.7，创建前需要人工确认')
  }

  if (plan.description && (plan.description.length < 60 || plan.description.length > 220)) {
    warnings.push('description 建议控制在 100 到 200 字')
  }

  if (plan.bodyMarkdown?.trim().startsWith('---')) {
    blockingErrors.push('bodyMarkdown 不能包含 Front Matter')
  }

  for (const key of ['tags', 'outline', 'imagePlaceholders', 'missingInfoQuestions', 'riskFlags', 'reviewChecklist'] as const) {
    if (!Array.isArray(plan[key])) {
      blockingErrors.push(`${key} 必须是数组`)
    }
  }

  return {
    valid: blockingErrors.length === 0,
    blockingErrors,
    warnings
  }
}

export function validateEditOperation(
  value: unknown,
  scopeText: string
): ValidationResult {
  const blockingErrors: string[] = []
  const warnings: string[] = []

  if (!isRecord(value)) {
    return {
      valid: false,
      blockingErrors: ['AI 返回内容不是有效对象'],
      warnings
    }
  }

  const operation = value as Partial<AIEditOperation>
  const validTypes = ['insert', 'replace', 'delete', 'rewrite', 'frontmatter', 'clarify', 'reject']
  const validScopes = ['selection', 'cursor', 'document', 'frontmatter']

  if (!operation.schemaVersion) blockingErrors.push('缺少 schemaVersion')
  if (!operation.type || !validTypes.includes(operation.type)) blockingErrors.push('编辑操作类型不合法')
  if (!operation.scope || !validScopes.includes(operation.scope)) blockingErrors.push('编辑作用范围不合法')
  if (!operation.summary) blockingErrors.push('缺少改动摘要')

  if (operation.type === 'insert' && !operation.newText) {
    blockingErrors.push('插入操作缺少 newText')
  }

  if (operation.type === 'replace') {
    if (!operation.oldText || !operation.newText) {
      blockingErrors.push('替换操作必须包含 oldText 和 newText')
    } else if (!scopeText.includes(operation.oldText)) {
      blockingErrors.push('oldText 不在当前作用范围内')
    }
  }

  if (operation.type === 'delete') {
    if (!operation.oldText) {
      blockingErrors.push('删除操作必须包含 oldText')
    } else if (!scopeText.includes(operation.oldText)) {
      blockingErrors.push('oldText 不在当前作用范围内')
    }
  }

  if (operation.type === 'rewrite' && !operation.newText) {
    blockingErrors.push('全文重写必须包含 newText')
  }

  if (operation.type === 'frontmatter' && !operation.frontMatterPatch) {
    blockingErrors.push('Front Matter 修改必须包含 frontMatterPatch')
  }

  if (typeof operation.confidence === 'number' && operation.confidence < 0.7) {
    warnings.push('编辑建议置信度较低')
  }

  return {
    valid: blockingErrors.length === 0,
    blockingErrors,
    warnings
  }
}
