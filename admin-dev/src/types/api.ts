/**
 * 统一 API 类型定义
 * 用于统一 GitHub API 和本地 API 的调用
 */

/**
 * 模式类型
 */
export type ModeType = 'online' | 'local'

/**
 * Front Matter 结构
 */
export interface FrontMatter {
  title: string
  date: string
  updated?: string
  categories: string[]
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
  fullPath?: string
  /** SHA 值（仅在线模式） */
  sha?: string
  /** 文章标题 */
  title: string
  /** 一级分类 */
  category: string
  /** 二级分类 */
  subCategory?: string
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
  /** 文件大小 */
  size?: number
  /** 最后修改时间 */
  lastModified?: string
}

/**
 * 文章详情
 */
export interface PostDetail extends PostInfo {
  /** 文章内容（原始 Markdown） */
  content: string
  /** Front matter 对象 */
  frontMatter?: FrontMatter
  /** 文章正文内容（不含 front matter） */
  body?: string
}

/**
 * 图片信息
 */
export interface ImageInfo {
  /** 图片路径 */
  path: string
  /** 图片文件名 */
  name: string
  /** 图片大小（字节） */
  size: number
  /** 图片 MIME 类型 */
  mimeType?: string
  /** 图片访问 URL */
  url?: string
  /** SHA 值（仅在线模式） */
  sha?: string
  /** 最后修改时间 */
  lastModified?: string
}

/**
 * 目录项
 */
export interface DirectoryItem {
  name: string
  path: string
  type: 'file' | 'dir'
  sha?: string
  size?: number
  downloadUrl?: string | null
}

/**
 * Git 操作结果
 */
export interface GitOperationResult {
  success: boolean
  message: string
  /** 提交哈希 */
  commitHash?: string
  /** HTML URL */
  htmlUrl?: string
}

/**
 * 统一 API 接口
 * 定义 GitHub API 和本地 API 的统一接口
 */
export interface BlogAPI {
  // ==================== 文章管理 ====================

  /**
   * 获取所有文章列表
   */
  getPosts(): Promise<PostInfo[]>

  /**
   * 获取单个文章信息
   * @param path 文章路径
   */
  getPost(path: string): Promise<PostInfo | PostDetail | null>

  /**
   * 获取文章原始内容
   * @param path 文章路径
   */
  getPostContent?(path: string): Promise<string>

  /**
   * 创建新文章
   * @param path 文件路径
   * @param content 文章内容
   * @param options 可选参数（prefix1/prefix2 用于本地模式调用 hexo np）
   */
  createPost(path: string, content: string, options?: { prefix1?: string; prefix2?: string; title?: string }): Promise<PostInfo | PostDetail | GitOperationResult>

  /**
   * 更新文章
   * @param path 文章路径
   * @param content 文章内容
   * @param sha 文件 SHA 值（仅在线模式需要）
   */
  updatePost(path: string, content: string, sha?: string): Promise<PostInfo | PostDetail | GitOperationResult>

  /**
   * 删除文章
   * @param path 文章路径
   * @param sha 文件 SHA 值（仅在线模式需要）
   */
  deletePost(path: string, sha?: string): Promise<void | GitOperationResult>

  /**
   * 获取分类目录列表
   */
  getCategories?(): Promise<DirectoryItem[]>

  /**
   * 获取指定分类下的文章列表
   * @param category 分类名称
   */
  getPostsByCategory?(category: string): Promise<PostInfo[]>

  // ==================== 图片管理 ====================

  /**
   * 上传图片
   * @param path 图片路径（GitHub 模式）或文章路径（本地模式）
   * @param content 图片数据
   * @param filename 图片文件名（仅本地模式需要）
   */
  uploadImage(path: string, content: Uint8Array | ArrayBuffer, filename?: string): Promise<ImageInfo | GitOperationResult>

  /**
   * 删除图片
   * @param path 图片路径
   * @param sha 文件 SHA 值（仅在线模式需要）
   */
  deleteImage(path: string, sha?: string): Promise<void | GitOperationResult>

  /**
   * 获取图片列表
   * @param articlePath 文章路径（仅本地模式需要）
   */
  getImages?(articlePath: string): Promise<ImageInfo[]>

  // ==================== Git 操作 ====================

  /**
   * 提交更改
   * @param message 提交信息
   */
  commit?(message: string): Promise<GitOperationResult>

  /**
   * 推送到远程
   */
  push?(): Promise<GitOperationResult>

  /**
   * 部署（commit + push）
   * @param message 提交信息
   * @param filePath 指定提交的文件路径（相对于仓库根目录），为空则提交所有变更
   */
  deploy(message: string, filePath?: string): Promise<GitOperationResult>

  // ==================== 工具方法 ====================

  /**
   * 检查文件是否存在
   * @param path 文件路径
   */
  fileExists?(path: string): Promise<boolean>

  /**
   * 获取目录内容
   * @param path 目录路径
   */
  getDirectoryContents?(path: string): Promise<DirectoryItem[]>

  /**
   * 检查服务是否可用
   */
  checkHealth?(): Promise<boolean>
}

/**
 * API 错误
 */
export interface APIError {
  code: string
  message: string
  details?: string
  originalError?: unknown
}