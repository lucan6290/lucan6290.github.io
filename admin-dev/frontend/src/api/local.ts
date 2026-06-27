import axios, { AxiosError } from 'axios'
import type { AxiosInstance, AxiosRequestConfig } from 'axios'
import type {
  LocalAPIError,
  LocalAPIErrorCode,
  PostInfo,
  PostDetail,
  ImageInfo,
  ImageFolderInfo,
  AssetCleanupResult,
  GitOperationResult,
  APIResponse,
  BackendAPIResponseError,
  RetryConfig
} from '@/types/local'
import type {
  AIChatRequest,
  AIChatResponse,
  AgentCommitRequest,
  AgentCommitResponse,
  AgentPlanRequest,
  AgentPlanResponse,
  ArticleIndexScanResult,
  ArticleIndexSummary,
  CategoryRegistryItem,
  EditApplyRequest,
  EditPlanRequest,
  EditPlanResponse,
  KnowledgeQARequest,
  KnowledgeQAResponse,
  WritingMaterialExtractResponse
} from '@/types/ai-writing'
import { LocalAPIErrorCode as ErrorCode } from '@/types/local'
import { parseFrontMatter } from '@/utils/frontmatter'

/**
 * 本地 API 配置
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:15000'
const ADMIN_API_PREFIX = '/api/admin/v1'

const LOCAL_API_CONFIG = {
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
}

/**
 * 默认重试配置
 */
const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  retryDelay: 1000,
  backoffFactor: 2
}

/**
 * 创建本地 API 错误
 */
function createAPIError(
  code: LocalAPIErrorCode,
  message: string,
  details?: string,
  originalError?: unknown
): LocalAPIError {
  return {
    code,
    message,
    details,
    originalError
  }
}

function isKnownErrorCode(code: unknown): code is LocalAPIErrorCode {
  return typeof code === 'string'
    && Object.values(ErrorCode).includes(code as LocalAPIErrorCode)
}

function stringifyDetails(details: unknown): string | undefined {
  if (details === undefined || details === null) return undefined
  if (typeof details === 'string') return details
  try {
    return JSON.stringify(details)
  } catch {
    return String(details)
  }
}

function normalizeResponseError(
  error: BackendAPIResponseError | undefined,
  fallbackMessage: string
): { code?: LocalAPIErrorCode; message: string; details?: string } {
  if (typeof error === 'string') {
    return {
      message: error,
      details: error
    }
  }

  if (typeof error === 'object' && error !== null) {
    return {
      code: isKnownErrorCode(error.code) ? error.code : undefined,
      message: error.message || fallbackMessage,
      details: stringifyDetails(error.details)
    }
  }

  return {
    message: fallbackMessage
  }
}

function apiPath(path: string): string {
  return `${ADMIN_API_PREFIX}${path}`
}

/**
 * 从 Axios 错误中提取错误信息
 */
function extractErrorFromAxios(error: AxiosError): LocalAPIError {
  if (!error.response) {
    // 网络错误
    return createAPIError(
      ErrorCode.NETWORK_ERROR,
      '网络连接失败',
      `无法连接到本地后端服务，请确保服务已启动（${API_BASE_URL}）`,
      error
    )
  }

  const status = error.response.status
  const data = error.response.data as {
    success?: boolean
    message?: string
    details?: unknown
    error?: BackendAPIResponseError
  }
  const responseError = normalizeResponseError(
    data?.error,
    data?.message || '本地后端请求失败'
  )
  const responseDetails = responseError.details || stringifyDetails(data?.details)
  const responseCode = responseError.code

  switch (status) {
    case 404:
      return createAPIError(
        responseCode || ErrorCode.FILE_NOT_FOUND,
        responseError.message || '文件不存在',
        responseDetails || '请求的资源未找到',
        error
      )
    case 403:
      return createAPIError(
        responseCode || ErrorCode.PERMISSION_DENIED,
        responseError.message || '权限不足',
        responseDetails || '没有权限执行此操作',
        error
      )
    case 400:
      return createAPIError(
        responseCode || ErrorCode.VALIDATION_ERROR,
        responseError.message || '参数验证失败',
        responseDetails || '请求参数无效',
        error
      )
    case 500:
    case 502:
    case 503:
      return createAPIError(
        responseCode || ErrorCode.SERVER_ERROR,
        responseError.message || '服务器错误',
        responseDetails || '本地后端服务发生错误',
        error
      )
    default:
      return createAPIError(
        responseCode || ErrorCode.UNKNOWN_ERROR,
        responseError.message || `请求失败 (${status})`,
        responseDetails || '发生未知错误',
        error
      )
  }
}

/**
 * 延迟函数
 */
function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * 带重试的请求执行器
 */
async function executeWithRetry<T>(
  requestFn: () => Promise<T>,
  config: RetryConfig = DEFAULT_RETRY_CONFIG
): Promise<T> {
  let lastError: Error | null = null
  let currentDelay = config.retryDelay

  for (let attempt = 1; attempt <= config.maxRetries; attempt++) {
    try {
      return await requestFn()
    } catch (error) {
      lastError = error as Error

      // 如果是 Axios 错误，检查是否应该重试
      if (axios.isAxiosError(error)) {
        const apiError = extractErrorFromAxios(error)

        // 这些错误不应该重试
        if (
          apiError.code === ErrorCode.FILE_NOT_FOUND ||
          apiError.code === ErrorCode.PERMISSION_DENIED ||
          apiError.code === ErrorCode.VALIDATION_ERROR
        ) {
          throw apiError
        }

        // 网络错误或服务器错误可以重试
        if (attempt < config.maxRetries) {
          console.warn(`请求失败，第 ${attempt} 次重试...`, {
            error: apiError.message,
            nextRetryIn: currentDelay
          })
          await delay(currentDelay)
          currentDelay *= config.backoffFactor || 2
          continue
        }
      }

      // 非 Axios 错误，直接抛出
      if (attempt === config.maxRetries) {
        throw lastError
      }
    }
  }

  throw lastError || new Error('重试次数已用尽')
}

/**
 * 本地 API 客户端类
 */
class LocalAPIClient {
  private client: AxiosInstance
  private retryConfig: RetryConfig

  constructor() {
    this.client = axios.create(LOCAL_API_CONFIG)
    this.retryConfig = DEFAULT_RETRY_CONFIG

    // 设置响应拦截器
    this.setupInterceptors()
  }

  /**
   * 设置 Axios 拦截器
   */
  private setupInterceptors(): void {
    // 响应拦截器 - 统一处理错误
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        const apiError = extractErrorFromAxios(error)
        console.error('[LocalAPI Error]', apiError)
        return Promise.reject(apiError)
      }
    )
  }

  /**
   * 执行请求（带重试）
   * 后端返回格式为 { success: boolean, data: T }，需要提取 data 字段
   */
  private async request<T>(config: AxiosRequestConfig): Promise<T> {
    return executeWithRetry(
      () => this.client.request<APIResponse<T>>(config).then(res => {
        const payload = res.data
        if (!payload.success) {
          const error = normalizeResponseError(payload.error, '本地后端请求失败')
          throw createAPIError(
            error.code || ErrorCode.SERVER_ERROR,
            error.message,
            error.details || error.message
          )
        }
        return payload.data as T
      }),
      this.retryConfig
    )
  }

  // ==================== 文章管理 API ====================

  /**
   * 获取所有文章列表
   */
  async getPosts(): Promise<PostInfo[]> {
    return this.request<PostInfo[]>({
      method: 'GET',
      url: apiPath('/posts')
    })
  }

  /**
   * 获取分类注册表
   */
  async getCategoryRegistry(): Promise<CategoryRegistryItem[]> {
    return this.request<CategoryRegistryItem[]>({
      method: 'GET',
      url: apiPath('/categories/registry')
    })
  }

  async updateCategoryRegistry(registry: CategoryRegistryItem[]): Promise<CategoryRegistryItem[]> {
    return this.request<CategoryRegistryItem[]>({
      method: 'PUT',
      url: apiPath('/categories/registry'),
      data: registry
    })
  }

  /**
   * 读取单个文章内容
   * @param path 文章相对路径（如 tech-study/ts-vue3-Vue3详解.md）
   */
  async getPost(path: string): Promise<PostDetail> {
    // 编码路径以处理特殊字符
    const encodedPath = encodeURIComponent(path)
    return this.request<PostDetail>({
      method: 'GET',
      url: apiPath(`/posts/${encodedPath}`)
    })
  }

  /**
   * 创建新文章
   * @param _path 文章相对路径（由 hexo np 自动生成）
   * @param _content 文章内容（由 hexo np 模板自动生成）
   * @param options 创建参数（title/prefix1/prefix2 用于调用 hexo np）
   */
  async createPost(_path: string, _content: string, options?: { prefix1?: string; prefix2?: string; title?: string }): Promise<PostDetail> {
    return this.request<PostDetail>({
      method: 'POST',
      url: apiPath('/posts'),
      data: {
        title: options?.title,
        prefix1: options?.prefix1,
        prefix2: options?.prefix2,
      }
    })
  }

  /**
   * 更新文章内容
   * @param path 文章相对路径
   * @param content 文章内容（Markdown）
   */
  async updatePost(path: string, content: string): Promise<PostDetail> {
    // 解析 Front Matter
    const { frontMatter, body } = parseFrontMatter(content)
    const encodedPath = encodeURIComponent(path)

    return this.request<PostDetail>({
      method: 'PUT',
      url: apiPath(`/posts/${encodedPath}`),
      data: {
        frontMatter,
        content: body
      }
    })
  }

  /**
   * 删除文章
   * @param path 文章相对路径
   */
  async deletePost(path: string): Promise<void> {
    const encodedPath = encodeURIComponent(path)
    return this.request<void>({
      method: 'DELETE',
      url: apiPath(`/posts/${encodedPath}`)
    })
  }

  // ==================== 图片管理 API ====================

  /**
   * 上传图片
   * @param articlePath 文章相对路径
   * @param imageData 图片数据（Uint8Array 或 Base64 字符串）
   * @param filename 图片文件名
   */
  async uploadImage(
    articlePath: string,
    imageData: Uint8Array | string,
    filename: string
  ): Promise<ImageInfo> {
    // 将 Uint8Array 转换为 Base64
    let base64Data: string
    if (typeof imageData === 'string') {
      base64Data = imageData
    } else {
      // 使用浏览器原生方法转换 Uint8Array 到 Base64
      const binary = Array.from(imageData)
        .map(byte => String.fromCharCode(byte))
        .join('')
      base64Data = btoa(binary)
    }

    // 从文件名提取扩展名
    const extension = filename.split('.').pop() || 'png'

    return this.request<ImageInfo>({
      method: 'POST',
      url: apiPath('/assets/images'),
      data: {
        articlePath,
        imageData: base64Data,
        extension
      }
    })
  }

  /**
   * 获取文章的所有图片
   * @param articlePath 文章相对路径
   */
  async getImages(articlePath: string): Promise<ImageInfo[]> {
    const encodedPath = encodeURIComponent(articlePath)
    return this.request<ImageInfo[]>({
      method: 'GET',
      url: apiPath(`/assets/images/${encodedPath}`)
    })
  }

  async getImageFolders(): Promise<ImageFolderInfo[]> {
    return this.request<ImageFolderInfo[]>({
      method: 'GET',
      url: apiPath('/assets/folders')
    })
  }

  async scanUnusedImages(articlePath: string, content: string): Promise<AssetCleanupResult> {
    return this.request<AssetCleanupResult>({
      method: 'POST',
      url: apiPath('/assets/unused'),
      data: {
        articlePath,
        content
      }
    })
  }

  async cleanupUnusedImages(articlePath: string, content: string): Promise<AssetCleanupResult> {
    return this.request<AssetCleanupResult>({
      method: 'POST',
      url: apiPath('/assets/cleanup-unused'),
      data: {
        articlePath,
        content
      }
    })
  }

  // ==================== AI 写作 API ====================

  async aiChat(payload: AIChatRequest): Promise<AIChatResponse> {
    return this.request<AIChatResponse>({
      method: 'POST',
      url: apiPath('/ai/chat'),
      data: payload
    })
  }

  async generateAgentPlan(payload: AgentPlanRequest): Promise<AgentPlanResponse> {
    return executeWithRetry(async () => {
      const res = await this.client.request<APIResponse<AgentPlanResponse>>({
        method: 'POST',
        url: apiPath('/ai/writing/agent/plan'),
        data: payload
      })
      if (res.data.data) return res.data.data
      const error = normalizeResponseError(res.data.error, '生成草稿方案失败')
      throw createAPIError(error.code || ErrorCode.SERVER_ERROR, error.message, error.details)
    })
  }

  async commitAgentPlan(payload: AgentCommitRequest): Promise<AgentCommitResponse> {
    return this.request<AgentCommitResponse>({
      method: 'POST',
      url: apiPath('/ai/writing/agent/commit'),
      data: payload
    })
  }

  async extractWritingMaterial(file: File): Promise<WritingMaterialExtractResponse> {
    const formData = new FormData()
    formData.append('file', file)
    return this.request<WritingMaterialExtractResponse>({
      method: 'POST',
      url: apiPath('/ai/writing/material/extract'),
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 60000
    })
  }

  async generateEditPlan(payload: EditPlanRequest): Promise<EditPlanResponse> {
    return executeWithRetry(async () => {
      const res = await this.client.request<APIResponse<EditPlanResponse>>({
        method: 'POST',
        url: apiPath('/ai/writing/edit/plan'),
        data: payload
      })
      if (res.data.data) return res.data.data
      const error = normalizeResponseError(res.data.error, '生成编辑方案失败')
      throw createAPIError(error.code || ErrorCode.SERVER_ERROR, error.message, error.details)
    })
  }

  async applyEditPlan(payload: EditApplyRequest): Promise<unknown> {
    return this.request<unknown>({
      method: 'POST',
      url: apiPath('/ai/writing/edit/apply'),
      data: payload
    })
  }

  async scanArticleIndex(): Promise<ArticleIndexScanResult> {
    return this.request<ArticleIndexScanResult>({
      method: 'POST',
      url: apiPath('/articles/index/scan'),
      data: {
        includeDrafts: true,
        force: true
      }
    })
  }

  async getArticleIndex(): Promise<ArticleIndexSummary> {
    const result = await this.request<ArticleIndexSummary>({
      method: 'GET',
      url: apiPath('/articles/index')
    })
    const articles = Array.isArray(result.articles) ? result.articles : []
    return {
      ...result,
      articleCount: result.articleCount ?? articles.length,
      draftCount: result.draftCount ?? articles.filter((item) => {
        return typeof item === 'object'
          && item !== null
          && 'status' in item
          && (item as { status?: unknown }).status === 'draft'
      }).length,
      failedFiles: result.failedFiles || [],
      indexStatus: result.indexStatus || 'ready'
    }
  }

  async knowledgeQA(payload: KnowledgeQARequest): Promise<KnowledgeQAResponse> {
    const result = await this.request<KnowledgeQAResponse>({
      method: 'POST',
      url: apiPath('/articles/knowledge-qa'),
      data: payload
    })
    return {
      ...result,
      warnings: (result.warnings || []).map((item: unknown) => {
        if (typeof item === 'string') return item
        if (typeof item === 'object' && item !== null && 'message' in item) {
          return String((item as { message?: unknown }).message || '')
        }
        return String(item)
      }),
      citations: (result.citations || []).map((citation) => ({
        ...citation,
        heading: citation.heading || citation.headingPath?.join(' / ') || ''
      }))
    }
  }

  /**
   * 删除图片
   * @param path 图片相对路径
   */
  async deleteImage(path: string): Promise<void> {
    const encodedPath = encodeURIComponent(path)
    return this.request<void>({
      method: 'DELETE',
      url: apiPath(`/assets/images/${encodedPath}`)
    })
  }

  // ==================== Git 操作 API ====================

  /**
   * 执行 git commit
   * @param message 提交信息
   */
  async commit(message: string): Promise<GitOperationResult> {
    return this.request<GitOperationResult>({
      method: 'POST',
      url: apiPath('/git/commit'),
      data: { message }
    })
  }

  /**
   * 执行 git push
   */
  async push(): Promise<GitOperationResult> {
    return this.request<GitOperationResult>({
      method: 'POST',
      url: apiPath('/git/push')
    })
  }

  /**
   * 一键部署：直接调用后端 /api/admin/v1/git/deploy（commit + push）
   * @param message 提交信息
   * @param filePath 指定提交的文件路径，为空则提交所有变更
   */
  async deploy(message: string, filePath?: string): Promise<GitOperationResult> {
    const result = await this.request<{ commit?: { stdout: string }; push?: { stdout: string } } | null>({
      method: 'POST',
      url: apiPath('/git/deploy'),
      data: { message, filePath }
    })
    return {
      success: !!result,
      message: result ? '部署成功' : '部署失败',
    }
  }

  // ==================== 工具方法 ====================

  /**
   * 检查本地服务是否可用
   */
  async checkHealth(): Promise<boolean> {
    try {
      await this.client.get(apiPath('/health'), { timeout: 5000 })
      return true
    } catch {
      return false
    }
  }

  /**
   * 设置重试配置
   */
  setRetryConfig(config: Partial<RetryConfig>): void {
    this.retryConfig = { ...this.retryConfig, ...config }
  }
}

// 导出单例实例
export const localAPI = new LocalAPIClient()

// 导出类型
export type {
  LocalAPIError,
  PostInfo,
  PostDetail,
  ImageInfo,
  AssetCleanupResult,
  GitOperationResult,
  APIResponse,
  RetryConfig
}

// 导出常量和工具函数
export { ErrorCode as LocalAPIErrorCode, createAPIError }
