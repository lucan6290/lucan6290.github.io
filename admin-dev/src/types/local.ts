/**
 * 本地 API 类型定义
 */

/**
 * 本地 API 错误类型
 */
export interface LocalAPIError {
  code: LocalAPIErrorCode
  message: string
  details?: string
  originalError?: unknown
}

/**
 * 错误代码常量
 */
export const LocalAPIErrorCode = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  FILE_NOT_FOUND: 'FILE_NOT_FOUND',
  PERMISSION_DENIED: 'PERMISSION_DENIED',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  SERVER_ERROR: 'SERVER_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR'
} as const

export type LocalAPIErrorCode = typeof LocalAPIErrorCode[keyof typeof LocalAPIErrorCode]

/**
 * 文章信息
 * 与 GitHub API 保持一致的接口
 */
export interface PostInfo {
  /** 文件路径（相对路径） */
  path: string
  /** 文件名（不含扩展名） */
  filename: string
  /** 文件大小（字节） */
  size: number
  /** SHA 哈希值（本地模式下可能为空或模拟值） */
  sha?: string
  /** 最后修改时间 */
  lastModified?: string
  /** 文章标题（从 front matter 解析） */
  title?: string
  /** 文章分类 */
  categories?: string[]
  /** 文章标签 */
  tags?: string[]
  /** 文章状态 */
  status?: 'draft' | 'wip' | 'published'
}

/**
 * 文章详情
 */
export interface PostDetail extends PostInfo {
  /** 文章内容（原始 Markdown） */
  content: string
  /** Front matter 对象 */
  frontMatter?: Record<string, unknown>
  /** 文章正文内容（不含 front matter） */
  body?: string
}

/**
 * 图片信息
 */
export interface ImageInfo {
  /** 图片路径（相对路径） */
  path: string
  /** 图片文件名 */
  name: string
  /** 图片大小（字节） */
  size: number
  /** 图片 MIME 类型 */
  mimeType: string
  /** 图片访问 URL */
  url: string
  /** 最后修改时间 */
  lastModified?: string
}

/**
 * Git 操作结果
 */
export interface GitOperationResult {
  success: boolean
  message: string
  /** 提交哈希（仅 commit 操作返回） */
  commitHash?: string
}

/**
 * API 响应包装
 */
export interface APIResponse<T> {
  success: boolean
  data?: T
  error?: LocalAPIError
}

/**
 * 重试配置
 */
export interface RetryConfig {
  /** 最大重试次数 */
  maxRetries: number
  /** 重试延迟（毫秒） */
  retryDelay: number
  /** 指数退避基数 */
  backoffFactor?: number
}