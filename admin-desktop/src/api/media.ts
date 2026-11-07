import { request } from './content'

export interface ArticleImage {
  relative_path: string
  name: string
  mime_type: string
  size: number
  markdown: string
}

export interface MediaDeletePlan {
  relative_path: string
  plan_id: string
  references: { relative_path: string; count: number }[]
}

const base = '/api/v1/media'

export const mediaApi = {
  list: (documentPath: string) =>
    request<{ images: ArticleImage[] }>(base + '?' + new URLSearchParams({ document_path: documentPath })),
  add: (documentPath: string, filename: string, data: string) =>
    request<ArticleImage>(base, 'POST', { document_path: documentPath, filename, data_base64: data }),
  deletePlan: (path: string) =>
    request<MediaDeletePlan>(base + '/delete-plan?' + new URLSearchParams({ path })),
  remove: (plan: MediaDeletePlan) =>
    request<{ deleted: string }>(base, 'DELETE', { relative_path: plan.relative_path, plan_id: plan.plan_id, confirm: true }),
}
