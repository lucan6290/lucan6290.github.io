import type { ContentDetail, ContentDirectory, ContentHealth, ContentIndex, ContentVersion } from '@/types/content'

let connection = { base_url: 'http://127.0.0.1:18000', token: '' }

export function setContentConnection(base_url: string, token: string) {
  connection = { base_url: base_url.replace(/\/+$/, ''), token }
}

export function getContentConnection() {
  return { ...connection }
}

export class ContentApiError extends Error {
  constructor(public status: number, public code: string, message: string, public details?: unknown) {
    super(message)
    this.name = 'ContentApiError'
  }
}

async function request<T>(path: string, method = 'GET', data?: unknown): Promise<T> {
  const response = await fetch(`${connection.base_url}${path}`, {
    method,
    headers: {
      ...(data === undefined ? {} : { 'Content-Type': 'application/json' }),
      ...(connection.token && path !== '/health' ? { Authorization: `Bearer ${connection.token}` } : {})
    },
    ...(data === undefined ? {} : { body: JSON.stringify(data) }),
    signal: AbortSignal.timeout(15000)
  })
  const result = await response.json()
  if (!response.ok) throw new ContentApiError(response.status, result.code || 'HTTP_ERROR', result.message || `请求失败 (${response.status})`, result.details)
  return result as T
}

export const contentApi = {
  health: () => request<ContentHealth>('/health'),
  list: () => request<ContentIndex>('/api/v1/content'),
  read: (path: string) => request<ContentDetail>(`/api/v1/documents?${new URLSearchParams({ path })}`),
  version: (path: string) => request<ContentVersion>(`/api/v1/documents/version?${new URLSearchParams({ path })}`),
  create: (path: string, raw: string, article = true) => request<ContentDetail>('/api/v1/documents', 'POST', { relative_path: path, raw_content: raw, article }),
  save: (path: string, raw: string, version: string, article?: boolean) => request<ContentDetail>('/api/v1/documents', 'PUT', { relative_path: path, raw_content: raw, expected_version: version, ...(article === undefined ? {} : { article }) }),
  remove: (path: string, version: string) => request<{ deleted: string }>('/api/v1/documents', 'DELETE', { relative_path: path, expected_version: version, confirm: true }),
  createDirectory: (path: string) => request<ContentDirectory>('/api/v1/directories', 'POST', { relative_path: path })
}
