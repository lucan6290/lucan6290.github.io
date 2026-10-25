import type { PostInfo, ValidationIssue } from '@/types/api'

export type PostDisplayStatus = 'ok' | 'warning' | 'error'

export interface PostDisplayStatusMeta {
  value: PostDisplayStatus
  label: string
  tagType: 'success' | 'warning' | 'error'
}

export function resolveIssueStatus(issues: ValidationIssue[] | undefined): PostDisplayStatusMeta {
  if (issues?.some((issue) => issue.severity === 'error')) {
    return { value: 'error', label: '需处理', tagType: 'error' }
  }
  if (issues?.some((issue) => issue.severity === 'warning')) {
    return { value: 'warning', label: '有提醒', tagType: 'warning' }
  }
  return { value: 'ok', label: '正常', tagType: 'success' }
}

export function getPostCategoryKey(post: PostInfo): string {
  if (post.categoryKey) return post.categoryKey
  if (post.categoryPath?.length) return post.categoryPath.join('/')
  if (post.category) return post.subCategory ? `${post.category}/${post.subCategory}` : post.category
  return post.type || 'uncategorized'
}

export function getPostCategoryLabel(post: PostInfo): string {
  if (post.categoryLabel) return post.categoryLabel
  if (post.categories?.length) return post.categories.filter(Boolean).join(' / ')
  if (post.category) return post.subCategory ? `${post.category} / ${post.subCategory}` : post.category
  return post.typeLabel || post.type || '未分类'
}

export function getPostPrimaryCategoryKey(post: PostInfo): string {
  return post.categoryPath?.[0] || post.category || post.type || 'uncategorized'
}

export function getPostPrimaryCategoryLabel(post: PostInfo): string {
  if (post.categoryPath && post.categoryPath.length <= 1 && post.categoryLabel) return post.categoryLabel
  return post.categories?.[0] || post.categoryLabel || post.typeLabel || post.type || '未分类'
}

export function getPostSecondaryCategoryKey(post: PostInfo): string {
  return post.categoryPath?.[1] || post.subCategory || ''
}

export function getPostSecondaryCategoryLabel(post: PostInfo): string {
  return post.categories?.[1] || getPostSecondaryCategoryKey(post) || '根目录'
}

export function getPostDisplayStatus(post: PostInfo): PostDisplayStatusMeta {
  if (post.displayStatus && post.displayStatusLabel) {
    const tagType = post.displayStatus === 'error' ? 'error' : post.displayStatus === 'warning' ? 'warning' : 'success'
    return { value: post.displayStatus, label: post.displayStatusLabel, tagType }
  }
  return resolveIssueStatus(post.issues)
}
