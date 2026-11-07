import { ContentApiError, request } from './content'
import type { AiOperation } from '../utils/aiDraft'

interface AiSettings {
  base_url: string
  model: string
  key_mode: 'none' | 'session' | 'windows'
  supports_windows_storage: boolean
}

interface AiSettingsUpdate {
  base_url: string
  model: string
  api_key?: string
  key_mode?: 'session' | 'windows' | 'clear'
}

const path = '/api/v1/ai'
const providerTimeout = 65000

export const aiWritingApi = {
  settings: () => request<AiSettings>(path + '/settings'),
  saveSettings: (data: AiSettingsUpdate) => request<AiSettings>(path + '/settings', 'PUT', data),
  test: () => request<{ ok: true }>(path + '/test', 'POST', undefined, providerTimeout),
  compose: (operation: AiOperation, instruction: string, body?: string) =>
    request<{ markdown: string }>(path + '/compose', 'POST', { operation, instruction, body }, providerTimeout)
}

export function aiErrorMessage(error: unknown, fallback: string) {
  if (error instanceof ContentApiError) return error.message
  if (error instanceof DOMException && error.name === 'TimeoutError') return '请求超时，请检查服务连接后重试。'
  return fallback
}