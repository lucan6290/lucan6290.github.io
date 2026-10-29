import type { ValidationIssue } from '@/types/api'

export interface DisplayStatusResult {
  value: 'ok' | 'warning' | 'error'
  label: string
}

export function resolveIssueStatus(issues: ValidationIssue[]): DisplayStatusResult {
  if (!issues || issues.length === 0) {
    return { value: 'ok', label: '正常' }
  }

  const hasError = issues.some((i) => i.severity === 'error')
  const hasWarning = issues.some((i) => i.severity === 'warning')

  if (hasError) return { value: 'error', label: '错误' }
  if (hasWarning) return { value: 'warning', label: '警告' }
  return { value: 'ok', label: '正常' }
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
  } catch {
    return dateStr
  }
}

export function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateStr
  }
}
