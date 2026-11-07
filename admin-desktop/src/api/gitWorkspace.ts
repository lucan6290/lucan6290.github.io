import { request } from '@/api/content'

export type GitAction = 'commit' | 'update' | 'push' | 'publish'

export interface GitChange {
  path: string
  staged: string
  unstaged: string
  conflicted: boolean
  selectable: boolean
}

export interface GitStatus {
  branch: string | null
  head: string | null
  upstream: { remote: string; branch: string; ahead: number | null; behind: number | null } | null
  operation: string | null
  changes: GitChange[]
  publish_configured: boolean
}

export interface GitDiff {
  path: string
  staged: string
  unstaged: string
  truncated: boolean
}

export type GitPreviewInput = { action: 'commit'; paths: string[]; message: string } |
  { action: Exclude<GitAction, 'commit'> }

export interface GitPreview {
  token: string
  action: GitAction
  branch: string
  head: string | null
  target: string
  target_commit: string | null
  remote_head: string | null
  remote_address: string | null
  paths: string[]
  message: string | null
  patch: string
  truncated: boolean
}

export interface GitResult {
  action: GitAction
  message: string
  commit: string | null
}

const base = '/api/v1/git'
export const gitWorkspaceApi = {
  status: () => request<GitStatus>(base + '/status'),
  diff: (path: string) => request<GitDiff>(base + '/diff?' + new URLSearchParams({ path })),
  preview: (input: GitPreviewInput) => request<GitPreview>(base + '/preview', 'POST', input, 65000),
  execute: (token: string) => request<GitResult>(base + '/execute', 'POST', { token, confirm: true }, 140000)
}
