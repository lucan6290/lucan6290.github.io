/**
 * GitHub API 相关类型定义
 */

/**
 * GitHub 文件信息
 */
export interface GitHubFile {
  name: string
  path: string
  sha: string
  size: number
  type: 'file' | 'dir' | 'symlink' | 'submodule'
  download_url: string | null
  html_url: string
  git_url: string
}

/**
 * GitHub 文件内容
 */
export interface GitHubContent {
  name: string
  path: string
  sha: string
  size: number
  type: 'file' | 'dir' | 'symlink' | 'submodule'
  encoding: string
  content: string
  download_url: string | null
  html_url: string
  git_url: string
}

/**
 * 文章 Front Matter
 */
export interface PostFrontMatter {
  title: string
  date: string
  updated?: string
  categories: [string, string] | string[]
  tags?: string[]
  description?: string
  layout?: string
  comments?: boolean
  permalink?: string
  excerpt?: string
  published?: boolean
  lang?: string
  cover?: string
  sticky?: number
  slug?: string
  status?: 'draft' | 'wip' | 'published'
  series?: string
  series_order?: number
}

/**
 * 文章信息
 */
export interface PostInfo {
  /** 文件名（不含扩展名） */
  filename: string
  /** 文件路径（相对于 source/_posts/） */
  path: string
  /** 完整路径（包含 source/_posts/） */
  fullPath: string
  /** SHA 值 */
  sha: string
  /** 文章标题 */
  title: string
  /** 一级分类 */
  category: string
  /** 二级分类 */
  subCategory: string
  /** 标签列表 */
  tags: string[]
  /** 创建日期 */
  date: string
  /** 更新日期 */
  updated?: string
  /** 文章状态 */
  status: 'draft' | 'wip' | 'published'
  /** 文章描述 */
  description?: string
  /** 封面图 */
  cover?: string
  /** 系列名称 */
  series?: string
  /** 系列顺序 */
  seriesOrder?: number
}

/**
 * 目录内容项
 */
export interface DirectoryItem {
  name: string
  path: string
  type: 'file' | 'dir'
  sha: string
  size: number
  downloadUrl: string | null
}

/**
 * 提交响应
 */
export interface CommitResponse {
  sha: string
  html_url: string
}

/**
 * 文件操作参数
 */
export interface FileOperationParams {
  path: string
  content: string
  message: string
  sha?: string
}

/**
 * GitHub API 错误
 */
export interface GitHubApiError {
  status: number
  message: string
  documentation_url?: string
}