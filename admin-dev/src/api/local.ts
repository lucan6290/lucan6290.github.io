import axios, { AxiosError } from 'axios'
import type { AxiosInstance, AxiosRequestConfig } from 'axios'
import type {
  LocalAPIError,
  LocalAPIErrorCode,
  PostInfo,
  PostDetail,
  ImageInfo,
  GitOperationResult,
  APIResponse,
  RetryConfig
} from '@/types/local'
import { LocalAPIErrorCode as ErrorCode } from '@/types/local'
import { parseFrontMatter } from '@/utils/frontmatter'

/**
 * 本地 API 配置
 */
const LOCAL_API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL,
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

/**
 * 从 Axios 错误中提取错误信息
 */
function extractErrorFromAxios(error: AxiosError): LocalAPIError {
  if (!error.response) {
    // 网络错误
    return createAPIError(
      ErrorCode.NETWORK_ERROR,
      '网络连接失败',
      `无法连接到本地后端服务，请确保服务已启动（${import.meta.env.VITE_API_BASE_URL}）`,
      error
    )
  }

  const status = error.response.status
  const data = error.response.data as { message?: string; error?: string }

  switch (status) {
    case 404:
      return createAPIError(
        ErrorCode.FILE_NOT_FOUND,
        '文件不存在',
        data?.message || '请求的资源未找到',
        error
      )
    case 403:
      return createAPIError(
        ErrorCode.PERMISSION_DENIED,
        '权限不足',
        data?.message || '没有权限执行此操作',
        error
      )
    case 400:
      return createAPIError(
        ErrorCode.VALIDATION_ERROR,
        '参数验证失败',
        data?.message || '请求参数无效',
        error
      )
    case 500:
    case 502:
    case 503:
      return createAPIError(
        ErrorCode.SERVER_ERROR,
        '服务器错误',
        data?.message || '本地后端服务发生错误',
        error
      )
    default:
      return createAPIError(
        ErrorCode.UNKNOWN_ERROR,
        `请求失败 (${status})`,
        data?.message || '发生未知错误',
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
      () => this.client.request<APIResponse<T>>(config).then(res => res.data.data as T),
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
      url: '/api/files/posts'
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
      url: `/api/files/post/${encodedPath}`
    })
  }

  /**
   * 创建新文章
   * @param _path 文章相对路径（本地模式下由 hexo np 自动生成）
   * @param _content 文章内容（本地模式下由 hexo np 模板自动生成）
   * @param options 创建参数（title/prefix1/prefix2 用于调用 hexo np）
   */
  async createPost(_path: string, _content: string, options?: { prefix1?: string; prefix2?: string; title?: string }): Promise<PostDetail> {
    return this.request<PostDetail>({
      method: 'POST',
      url: '/api/files/post',
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
      url: `/api/files/post/${encodedPath}`,
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
      url: `/api/files/post/${encodedPath}`
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
      url: '/api/assets/image',
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
      url: `/api/assets/images/${encodedPath}`
    })
  }

  /**
   * 删除图片
   * @param path 图片相对路径
   */
  async deleteImage(path: string): Promise<void> {
    const encodedPath = encodeURIComponent(path)
    return this.request<void>({
      method: 'DELETE',
      url: `/api/assets/image/${encodedPath}`
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
      url: '/api/git/commit',
      data: { message }
    })
  }

  /**
   * 执行 git push
   */
  async push(): Promise<GitOperationResult> {
    return this.request<GitOperationResult>({
      method: 'POST',
      url: '/api/git/push'
    })
  }

  /**
   * 一键部署：直接调用后端 /api/git/deploy（commit + push）
   * @param message 提交信息
   */
  async deploy(message: string): Promise<GitOperationResult> {
    const result = await this.request<{ commit?: { stdout: string }; push?: { stdout: string } } | null>({
      method: 'POST',
      url: '/api/git/deploy',
      data: { message }
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
      await this.client.get('/health', { timeout: 5000 })
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
  GitOperationResult,
  APIResponse,
  RetryConfig
}

// 导出常量和工具函数
export { ErrorCode as LocalAPIErrorCode, createAPIError }