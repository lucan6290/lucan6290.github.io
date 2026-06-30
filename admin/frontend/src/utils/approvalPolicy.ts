import type {
  AIApprovalMode,
  AIEditOperation,
  AIDraftPlan,
  ApprovalDecision,
  ValidationResult
} from '@/types/ai-writing'

const HIGH_RISK_FLAGS = [
  '分类不确定',
  '事实待验证',
  '信息不足',
  '可能包含敏感信息',
  '图片占位无法确认'
]

function collectRiskReasons(riskFlags: string[] = []): string[] {
  return riskFlags.filter(flag =>
    HIGH_RISK_FLAGS.some(highRisk => flag.includes(highRisk))
  )
}

export function resolveAgentApprovalDecision(
  selectedMode: AIApprovalMode,
  plan: AIDraftPlan | null,
  validation: ValidationResult | null,
  clarificationHandled: boolean
): ApprovalDecision {
  const reasons: string[] = []

  if (!validation?.valid) {
    reasons.push(...(validation?.blockingErrors || ['草稿方案校验失败']))
  }

  if (plan?.clarificationRequired && !clarificationHandled) {
    reasons.push('求证问题尚未处理')
  }

  if (plan && plan.confidence < 0.7) {
    reasons.push('方案置信度较低')
  }

  if (plan) {
    reasons.push(...collectRiskReasons(plan.riskFlags))
  }

  const blocked = !validation?.valid
  const downgraded = selectedMode !== 'request-approval' && reasons.length > 0
  const effectiveMode = downgraded ? 'request-approval' : selectedMode

  return {
    effectiveMode,
    requiresManualApproval: effectiveMode === 'request-approval' || reasons.length > 0,
    downgraded,
    blocked,
    reasons
  }
}

export function resolveEditApprovalDecision(
  selectedMode: AIApprovalMode,
  operation: AIEditOperation | null,
  validation: ValidationResult | null
): ApprovalDecision {
  const reasons: string[] = []

  if (!validation?.valid) {
    reasons.push(...(validation?.blockingErrors || ['编辑操作校验失败']))
  }

  if (operation) {
    if (operation.confidence < 0.7) reasons.push('编辑操作置信度较低')
    reasons.push(...collectRiskReasons(operation.riskFlags))

    if (operation.type === 'delete' || operation.type === 'rewrite') {
      reasons.push('删除或全文重写需要人工确认')
    }

    if (operation.type === 'reject' || operation.type === 'clarify') {
      reasons.push('AI 未生成可执行编辑操作')
    }
  }

  const blocked = !validation?.valid || operation?.type === 'reject' || operation?.type === 'clarify'
  const downgraded = selectedMode !== 'request-approval' && reasons.length > 0
  const effectiveMode = downgraded ? 'request-approval' : selectedMode

  return {
    effectiveMode,
    requiresManualApproval: effectiveMode === 'request-approval' || reasons.length > 0,
    downgraded,
    blocked,
    reasons
  }
}

