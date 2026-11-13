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

export async function request<T>(path: string, method = 'GET', data?: unknown, timeout = 15000): Promise<T> {
  const response = await fetch(`${connection.base_url}${path}`, {
    method,
    headers: {
      ...(data === undefined ? {} : { 'Content-Type': 'application/json' }),
      ...(connection.token && path !== '/health' ? { Authorization: `Bearer ${connection.token}` } : {})
    },
    ...(data === undefined ? {} : { body: JSON.stringify(data) }),
    signal: AbortSignal.timeout(timeout)
  })
  const result = await response.json()
  if (!response.ok) throw new ContentApiError(response.status, result.code || 'HTTP_ERROR', result.message || `请求失败 (${response.status})`, result.details)
  return result as T
}

export const contentApi = {
  health: (timeout?: number) => request<ContentHealth>('/health', 'GET', undefined, timeout),
  probe: (timeout: number) => request<ContentVersion>('/api/v1/documents/version?path=desktop-connection-probe.md', 'GET', undefined, timeout),
  list: (query = '') => request<ContentIndex>(query ? `/api/v1/content?${new URLSearchParams({ query })}` : '/api/v1/content'),
  async image(path: string, signal: AbortSignal) {
    const response = await fetch(`${connection.base_url}/api/v1/images?${new URLSearchParams({ path })}`, {
      headers: { Authorization: `Bearer ${connection.token}` },
      cache: 'no-store',
      signal: AbortSignal.any([signal, AbortSignal.timeout(15000)]),
    })
    if (!response.ok) throw new Error('无法读取预览图片')
    return response.blob()
  },
  read: (path: string) => request<ContentDetail>(`/api/v1/documents?${new URLSearchParams({ path })}`),
  version: (path: string) => request<ContentVersion>(`/api/v1/documents/version?${new URLSearchParams({ path })}`),
  create: (path: string, raw: string, article = true) => request<ContentDetail>('/api/v1/documents', 'POST', { relative_path: path, raw_content: raw, article }),
  save: (path: string, raw: string, version: string, article?: boolean) => request<ContentDetail>('/api/v1/documents', 'PUT', { relative_path: path, raw_content: raw, expected_version: version, ...(article === undefined ? {} : { article }) }),
  remove: (path: string, version: string) => request<{ deleted: string }>('/api/v1/documents', 'DELETE', { relative_path: path, expected_version: version, confirm: true }),
  createDirectory: (path: string) => request<ContentDirectory>('/api/v1/directories', 'POST', { relative_path: path })
}
