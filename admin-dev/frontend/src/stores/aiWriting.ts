import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { getAPI } from '@/api'
import type {
  AIApprovalMode,
  AIChatMessage,
  AIModelPayload,
  AIWritingError,
  AIWritingMode,
  AIDraftPlan,
  AIOperationLogItem,
  CategoryRegistryItem,
  ValidationResult
} from '@/types/ai-writing'
import { validateDraftPlan } from '@/utils/aiWritingValidation'
import { resolveAgentApprovalDecision } from '@/utils/approvalPolicy'

function fallbackCategory(
  prefix1: string,
  primaryName: string,
  primarySlug: string,
  cover: string,
  sortOrder: number
): CategoryRegistryItem {
  return {
    frontend_name1: primaryName,
    category_slug: primarySlug,
    note_prefix1: prefix1,
    cover,
    sort_order: sortOrder,
    enabled: true,
    children: [],
    prefix1,
    primaryName,
    primarySlug,
    dir: primarySlug
  }
}

export const FALLBACK_CATEGORY_REGISTRY: CategoryRegistryItem[] = [
  fallbackCategory('ts', '技术研习', 'tech-study', '/img/covers/tech-study.svg', 10),
  fallbackCategory('pr', '踩坑复盘', 'pitfall-review', '/img/covers/pitfall-review.svg', 20),
  fallbackCategory('pp', '项目实战', 'project-practice', '/img/covers/project-practice.svg', 30),
  fallbackCategory('ge', '成长随笔', 'growth-essay', '/img/covers/growth-essay.svg', 40),
  fallbackCategory('rs', '资源分享', 'resource-sharing', '/img/covers/resource-sharing.svg', 50)
]

function createSessionId(): string {
  return `aiw_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

function createError(code: string, title: string, message: string, retryable = true): AIWritingError {
  return { code, title, message, retryable }
}

const MAX_SESSION_HISTORY_MESSAGES = 8

export const useAIWritingStore = defineStore('aiWriting', () => {
  const activeMode = ref<AIWritingMode>('agent')
  const approvalMode = ref<AIApprovalMode>('request-approval')
  const sessionId = ref<string>(createSessionId())
  const isGenerating = ref(false)
  const isCreatingDraft = ref(false)
  const operationLog = ref<AIOperationLogItem[]>([])
  const registry = ref<CategoryRegistryItem[]>(FALLBACK_CATEGORY_REGISTRY)

  const agentInput = ref('')
  const saveAsInboxOnly = ref(false)
  const clarificationAnswers = ref<Record<string, string>>({})
  const continueWithCurrentUnderstanding = ref(false)
  const draftPlan = ref<AIDraftPlan | null>(null)
  const draftValidation = ref<ValidationResult | null>(null)
  const createResultPath = ref<string | null>(null)
  const agentError = ref<AIWritingError | null>(null)

  const llmInput = ref('')
  const llmHistory = ref<AIChatMessage[]>([])

  const agentDecision = computed(() =>
    resolveAgentApprovalDecision(
      approvalMode.value,
      draftPlan.value,
      draftValidation.value,
      Boolean(continueWithCurrentUnderstanding.value || Object.keys(clarificationAnswers.value).length > 0)
    )
  )

  function addLog(level: AIOperationLogItem['level'], title: string, detail?: string): void {
    operationLog.value.unshift({
      id: `log_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
      time: new Date().toLocaleString(),
      level,
      title,
      detail
    })
  }

  function resetSession(): void {
    sessionId.value = createSessionId()
    draftPlan.value = null
    draftValidation.value = null
    createResultPath.value = null
    agentError.value = null
    llmHistory.value = []
    clarificationAnswers.value = {}
    continueWithCurrentUnderstanding.value = false
    addLog('info', '已创建新的 AI 写作会话', sessionId.value)
  }

  function rememberAgentTurn(userInput: string, assistantContent: string): void {
    const nextHistory: AIChatMessage[] = [
      ...llmHistory.value,
      { role: 'user', content: userInput },
      { role: 'assistant', content: assistantContent }
    ]
    llmHistory.value = nextHistory.slice(-MAX_SESSION_HISTORY_MESSAGES)
  }

  function summarizePlanForHistory(plan: AIDraftPlan): string {
    const outline = plan.outline.slice(0, 5).join(' / ')
    return [
      `已生成草稿方案：${plan.title}`,
      `分类：${plan.primaryName} / ${plan.prefix2}`,
      `意图：${plan.userIntent}`,
      outline ? `大纲：${outline}` : '',
      plan.missingInfoQuestions.length ? `待补充：${plan.missingInfoQuestions.join('；')}` : ''
    ].filter(Boolean).join('\n')
  }

  async function fetchCategoryRegistry(): Promise<CategoryRegistryItem[]> {
    const api = getAPI()
    try {
      if (!api.getCategoryRegistry) {
        registry.value = FALLBACK_CATEGORY_REGISTRY
        return registry.value
      }
      registry.value = await api.getCategoryRegistry()
      addLog('success', '分类注册表已加载', `共 ${registry.value.length} 个一级分类`)
    } catch {
      registry.value = FALLBACK_CATEGORY_REGISTRY
      addLog('warning', '分类注册表接口不可用，已使用前端兜底配置')
    }
    return registry.value
  }

  async function generateAgentPlan(model: AIModelPayload): Promise<AIDraftPlan | null> {
    if (!agentInput.value.trim()) {
      agentError.value = createError('EMPTY_INPUT', '输入不能为空', '请先写下想法、笔记或素材。', false)
      return null
    }

    const api = getAPI()
    if (!api.generateAgentPlan) {
      agentError.value = createError('AI_API_MISSING', 'AI 接口不可用', '当前 API 适配器没有提供 generateAgentPlan 方法。')
      return null
    }

    isGenerating.value = true
    agentError.value = null
    addLog('info', '开始生成 Agent 草稿方案', `权限：${approvalMode.value}`)

    try {
      await fetchCategoryRegistry()
      const response = await api.generateAgentPlan({
        approvalMode: approvalMode.value,
        sessionId: sessionId.value,
        userInput: agentInput.value,
        writingGoal: 'auto',
        userPreferences: {
          saveAsInboxOnly: saveAsInboxOnly.value,
          continueWithCurrentUnderstanding: continueWithCurrentUnderstanding.value,
          categoryRegistry: registry.value
        },
        clarificationAnswers: Object.values(clarificationAnswers.value).filter(Boolean),
        conversationHistory: llmHistory.value.slice(-MAX_SESSION_HISTORY_MESSAGES),
        model
      })
      sessionId.value = response.sessionId || sessionId.value
      draftPlan.value = response.plan
      if (!response.plan) {
        draftValidation.value = {
          valid: false,
          blockingErrors: response.validationErrors?.length ? response.validationErrors : ['后端未返回草稿方案'],
          warnings: response.warnings || []
        }
        addLog('warning', '草稿方案未生成', draftValidation.value.blockingErrors.join('；'))
        rememberAgentTurn(agentInput.value, `草稿方案未生成：${draftValidation.value.blockingErrors.join('；')}`)
        return null
      }

      const localValidation = validateDraftPlan(response.plan, registry.value)
      draftValidation.value = {
        valid: localValidation.valid && !response.validationErrors?.length,
        blockingErrors: [...localValidation.blockingErrors, ...(response.validationErrors || [])],
        warnings: [...localValidation.warnings, ...(response.warnings || [])]
      }
      rememberAgentTurn(agentInput.value, summarizePlanForHistory(response.plan))
      addLog(draftValidation.value.valid ? 'success' : 'warning', '草稿方案已返回', draftValidation.value.valid ? response.plan.title : draftValidation.value.blockingErrors.join('；'))
      return response.plan
    } catch (error) {
      const message = error instanceof Error ? error.message : 'AI 返回格式异常或请求失败'
      agentError.value = createError('AI_RESPONSE_ERROR', '生成失败', message)
      addLog('error', '草稿方案生成失败', message)
      return null
    } finally {
      isGenerating.value = false
    }
  }

  return {
    activeMode,
    approvalMode,
    sessionId,
    isGenerating,
    isCreatingDraft,
    operationLog,
    registry,
    agentInput,
    saveAsInboxOnly,
    clarificationAnswers,
    continueWithCurrentUnderstanding,
    draftPlan,
    draftValidation,
    createResultPath,
    agentError,
    llmInput,
    llmHistory,
    agentDecision,
    addLog,
    resetSession,
    fetchCategoryRegistry,
    generateAgentPlan
  }
})
