/**
 * 管理端桌面 API 客户端
 *
 * 从 admin/frontend/src/api/local.ts 重构，适配 Tauri 桌面端：
 * - API base URL 动态获取（Tauri 注入端口或回退 18000）
 * - 直接 HTTP 请求，不经过 Vite proxy
 * - 简化的错误处理和重试
 */
import axios, { AxiosError } from 'axios'
import type { AxiosInstance, AxiosRequestConfig } from 'axios'
import type {
  BlogAPI, PostInfo, PostDetail, ImageInfo, ImageFolderInfo, GitOperationResult,
  CategoryDTO, TagDTO, GitStatusDTO, TaskDTO, PreviewStatusDTO, ValidationIssue,
  SiteValidationResultDTO, DocusaurusConfigStatusDTO, ContentSchemaDTO, SidebarStatusDTO,
  RegistryIndexSyncResultDTO, RegistryIndexStatsDTO, RegistryIndexListResponseDTO,
  RegistryYamlFileDTO, RegistryYamlEntriesDTO, RegistryDiffDTO, SearchResultDTO,
  SearchIndexResultDTO, AIModelConfigDTO, AIModelTestResultDTO, AIDraftResultDTO,
  AIRewriteResultDTO, GitSyncStatusDTO, GitCommandResultDTO, FetchWebResultDTO
} from '@/types/api'
import type { LocalAPIError, LocalAPIErrorCode, RetryConfig } from '@/types/local'
import { ErrorCode } from '@/types/local'
import { resolveIssueStatus } from '@/utils/postDisplay'
import { parseFrontMatter, stripLeadingBom } from '@/utils/frontmatter'
import { clearAuthSession, getAuthToken } from '@/utils/auth'

// 动态获取 API base URL
function getApiBaseUrl(): string {
  // Tauri 注入的端口优先
  if (typeof window !== 'undefined' && window.__BACKEND_PORT__) {
    return `http://127.0.0.1:${window.__BACKEND_PORT__}`
  }
  // 开发模式回退
  return import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:18000'
}

const API_PREFIX = '/api/v1'

const DEFAULT_RETRY: RetryConfig = {
  maxRetries: 3,
  retryDelay: 1000,
  backoffFactor: 2
}

// ---------- DTO 类型 ----------
type ArticleType = 'docs' | 'blog'

interface ValidationIssueDTO {
  code: string
  message: string
  severity: string
}

interface ArticleSummaryDTO {
  id: string
  type: ArticleType
  type_label?: string
  title: string | null
  description: string | null
  date?: string | null
  last_update?: { date?: string; author?: string } | null
  relative_path: string
  route: string
  slug: string
  tags: string[]
  authors: string[]
  category_path: string[]
  category_label: string
  sidebar_registered: boolean | null
  version: string
  updated_at: string
  issues: ValidationIssueDTO[]
}

interface ArticleListResponseDTO {
  items: ArticleSummaryDTO[]
  page: number
  page_size: number
  total: number
  has_next: boolean
}

interface ArticleDetailDTO extends ArticleSummaryDTO {
  frontmatter: Record<string, unknown>
  body: string
  raw_content: string
  image_dir: string | null
}

interface ImageDTO {
  name: string
  relative_path: string
  markdown_url: string
  markdown?: string
  size: number
  referenced?: boolean
  created_at?: string | null
}

interface ArticleImageListDTO {
  article_id: string
  image_dir: string | null
  images: ImageDTO[]
}

interface LoginResponseDTO {
  access_token: string
  token_type: string
  expires_at: number
  username: string
}

// ---------- 工具函数 ----------
function apiPath(path: string): string {
  return `${API_PREFIX}${path}`
}

function basenameWithoutExt(path: string): string {
  const name = path.split('/').pop() || path
  return name.replace(/\.[^.]+$/, '')
}

function normalizeStatus(frontmatter: Record<string, unknown>): 'draft' | 'wip' | 'published' {
  const status = frontmatter.status
  if (status === 'draft' || status === 'wip' || status === 'published') return status
  if (frontmatter.draft === true || frontmatter.published === false) return 'draft'
  return 'published'
}

function mapSummaryToPost(article: ArticleSummaryDTO): PostInfo {
  const categoryPath = article.category_path || []
  const issues = article.issues || []
  const displayStatus = resolveIssueStatus(issues)

  return {
    id: article.id,
    type: article.type,
    typeLabel: article.type_label || (article.type === 'blog' ? '博客' : '知识库'),
    filename: basenameWithoutExt(article.relative_path),
    path: article.id,
    fullPath: article.relative_path,
    sha: article.version,
    version: article.version,
    route: article.route,
    relativePath: article.relative_path,
    slug: article.slug,
    title: article.title || basenameWithoutExt(article.relative_path),
    category: categoryPath[0] || article.type,
    subCategory: categoryPath[1] || '',
    categories: categoryPath.length > 0 ? categoryPath : [article.category_label || article.type],
    tags: article.tags || [],
    authors: article.authors || [],
    date: article.date || article.updated_at,
    lastUpdate: article.last_update || undefined,
    status: displayStatus.value === 'error' ? 'wip' : 'published',
    description: article.description || undefined,
    lastModified: article.updated_at,
    categoryPath,
    categoryLabel: article.category_label,
    categoryKey: categoryPath.length > 0 ? categoryPath.join('/') : article.type,
    displayStatus: displayStatus.value,
    displayStatusLabel: displayStatus.label,
    sidebarRegistered: article.sidebar_registered,
    issues
  }
}

function mapDetailToPost(article: ArticleDetailDTO): PostDetail {
  const summary = mapSummaryToPost(article)
  const frontMatter = article.frontmatter || {}
  const content = stripLeadingBom(article.raw_content)

  return {
    ...summary,
    status: normalizeStatus(frontMatter),
    content,
    frontMatter: frontMatter as unknown as PostDetail['frontMatter'],
    body: article.body,
    imageDir: article.image_dir,
    unusedImages: []
  }
}

function mapImage(image: ImageDTO, articleId?: string): ImageInfo {
  return {
    path: image.relative_path,
    name: image.name,
    size: image.size,
    url: image.markdown_url,
    markdownUrl: image.markdown_url,
    markdown: image.markdown,
    referenced: image.referenced,
    lastModified: image.created_at || undefined,
    sha: articleId
  }
}

function inferImageMimeType(filename: string): string {
  const ext = filename.match(/\.[^.]+$/)?.[0]?.toLowerCase()
  const map: Record<string, string> = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.webp': 'image/webp',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml'
  }
  return map[ext || ''] || 'application/octet-stream'
}

function sanitizePathSegment(value: string): string {
  const seg = value.trim()
    .replace(/\.[^.]+$/, '')
    .replace(/[<>:"\\|?*\x00-\x1f/]+/g, '-')
    .replace(/\s+/g, '-')
    .replace(/-{2,}/g, '-')
    .replace(/^[.\s-]+|[.\s-]+$/g, '')
  return seg || `article-${Date.now()}`
}

function createAPIError(code: LocalAPIErrorCode, message: string, details?: string, originalError?: unknown): LocalAPIError {
  return { code, message, details, originalError }
}

function extractErrorFromAxios(error: AxiosError): LocalAPIError {
  if (!error.response) {
    return createAPIError(ErrorCode.NETWORK_ERROR, '网络连接失败', `无法连接到后端服务`, error)
  }
  const status = error.response.status
  const data = error.response.data as { code?: string; message?: string; details?: unknown }
  const message = data?.message || `请求失败 (${status})`
  const knownCode =
    status === 404 ? ErrorCode.FILE_NOT_FOUND :
    status === 403 ? ErrorCode.PERMISSION_DENIED :
    status === 400 || status === 409 || status === 422 || status === 428 ? ErrorCode.VALIDATION_ERROR :
    status >= 500 ? ErrorCode.SERVER_ERROR :
    ErrorCode.UNKNOWN_ERROR
  return createAPIError(knownCode, message, typeof data?.details === 'string' ? data.details : undefined, error)
}

function delay(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms))
}

async function executeWithRetry<T>(fn: () => Promise<T>, config: RetryConfig = DEFAULT_RETRY): Promise<T> {
  let lastError: unknown = null
  let currentDelay = config.retryDelay
  for (let attempt = 1; attempt <= config.maxRetries; attempt++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error
      const apiError = axios.isAxiosError(error) ? extractErrorFromAxios(error) : error as LocalAPIError
      const retryable = apiError.code === ErrorCode.NETWORK_ERROR || apiError.code === ErrorCode.SERVER_ERROR
      if (!retryable || attempt === config.maxRetries) throw apiError
      await delay(currentDelay)
      currentDelay *= config.backoffFactor || 2
    }
  }
  throw lastError
}

function mutationParams(options?: { dryRun?: boolean; confirm?: boolean }) {
  return { dry_run: options?.dryRun ?? false, confirm: options?.confirm ?? true }
}

// ---------- API 客户端 ----------
class DesktopAPIClient implements BlogAPI {
  private client: AxiosInstance
  private retryConfig: RetryConfig
  private loadedVersions = new Map<string, string>()
  private imageArticleMap = new Map<string, { articleId: string; imageName: string }>()

  constructor() {
    this.retryConfig = DEFAULT_RETRY
    this.client = axios.create({
      baseURL: getApiBaseUrl(),
      timeout: 30000,
      headers: { 'Content-Type': 'application/json' }
    })

    this.client.interceptors.request.use((config) => {
      // 动态更新 baseURL（Tauri sidecar 使用随机端口，模块加载时可能尚未注入）
      config.baseURL = getApiBaseUrl()
      const token = getAuthToken()
      if (token) {
        config.headers = { ...config.headers, Authorization: `Bearer ${token}` } as typeof config.headers
      }
      return config
    })

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError | LocalAPIError) => {
        if (axios.isAxiosError(error)) {
          if (error.response?.status === 401) clearAuthSession()
          return Promise.reject(extractErrorFromAxios(error))
        }
        return Promise.reject(error)
      }
    )
  }

  private async request<T>(config: AxiosRequestConfig): Promise<T> {
    return executeWithRetry(() => this.client.request<T>(config).then((r) => r.data), this.retryConfig)
  }

  async loginAdmin(username: string, password: string) {
    return this.request<LoginResponseDTO>({
      method: 'POST',
      url: apiPath('/auth/login'),
      data: { username, password }
    })
  }

  async checkHealth(): Promise<boolean> {
    try {
      await this.client.get(apiPath('/health'), { timeout: 5000 })
      return true
    } catch {
      return false
    }
  }

  async getPosts(): Promise<PostInfo[]> {
    const firstPage = await this.request<ArticleListResponseDTO>({
      method: 'GET',
      url: apiPath('/articles'),
      params: { page: 1, page_size: 100, sort: '-updated_at' }
    })
    const items = [...firstPage.items]
    let page = firstPage.page
    while (firstPage.has_next && items.length < firstPage.total) {
      page += 1
      const next = await this.request<ArticleListResponseDTO>({
        method: 'GET',
        url: apiPath('/articles'),
        params: { page, page_size: firstPage.page_size, sort: '-updated_at' }
      })
      items.push(...next.items)
      if (!next.has_next) break
    }
    return items.map(mapSummaryToPost)
  }

  async getPost(articleId: string): Promise<PostDetail> {
    const detail = await this.request<ArticleDetailDTO>({
      method: 'GET',
      url: apiPath(`/articles/${encodeURIComponent(articleId)}`)
    })
    this.loadedVersions.set(articleId, detail.version)
    return mapDetailToPost(detail)
  }

  async createPost(path: string, content: string, options?: import('@/types/api').ArticleCreateOptions): Promise<PostDetail> {
    const fallbackSlug = path ? basenameWithoutExt(path) : options?.title || 'untitled'
    const type = options?.type || 'docs'
    const categoryPath = options?.categoryPath || path.split('/').slice(0, -1).map(sanitizePathSegment).filter(Boolean)
    const detail = await this.request<ArticleDetailDTO>({
      method: 'POST',
      url: apiPath('/articles'),
      data: {
        type,
        title: options?.title || fallbackSlug,
        slug: sanitizePathSegment(options?.slug || fallbackSlug),
        description: options?.description || null,
        body: content || '',
        category_path: categoryPath,
        sidebar_position: options?.sidebarPosition ?? null,
        authors: type === 'blog' ? (options?.authors || ['lucan']) : [],
        tags: type === 'blog' ? (options?.tags || []) : [],
        date: options?.date || null,
        last_update: type === 'blog' ? (options?.lastUpdate || null) : null
      }
    })
    this.loadedVersions.set(detail.id, detail.version)
    return mapDetailToPost(detail)
  }

  async updatePost(articleId: string, content: string, expectedVersion?: string): Promise<PostDetail> {
    const { frontMatter, body } = parseFrontMatter(content)
    const detail = await this.request<ArticleDetailDTO>({
      method: 'PUT',
      url: apiPath(`/articles/${encodeURIComponent(articleId)}`),
      data: {
        frontmatter: frontMatter,
        body,
        validate_after_save: true,
        expected_version: expectedVersion || this.loadedVersions.get(articleId)
      }
    })
    this.loadedVersions.set(articleId, detail.version)
    return mapDetailToPost(detail)
  }

  async deletePost(articleId: string, _sha?: string, options?: import('@/types/api').ArticleDeleteOptions) {
    const result = await this.request<unknown>({
      method: 'DELETE',
      url: apiPath(`/articles/${encodeURIComponent(articleId)}`),
      params: { with_images: options?.withImages ?? false, ...mutationParams(options) }
    })
    if (options?.dryRun) return result
  }

  async movePost(articleId: string, options: import('@/types/api').ArticleMoveOptions) {
    return this.request({
      method: 'POST',
      url: apiPath(`/articles/${encodeURIComponent(articleId)}/move`),
      data: {
        target_type: options.targetType,
        target_slug: options.targetSlug,
        target_category_path: options.targetCategoryPath || [],
        target_date: options.targetDate ?? null,
        replace_links: options.replaceLinks ?? false,
        ...mutationParams(options)
      }
    })
  }

  async getImages(articleId: string): Promise<ImageInfo[]> {
    const result = await this.request<ArticleImageListDTO>({
      method: 'GET',
      url: apiPath(`/articles/${encodeURIComponent(articleId)}/images`)
    })
    for (const img of result.images) {
      this.imageArticleMap.set(img.relative_path, { articleId: result.article_id, imageName: img.name })
    }
    return result.images.map((img) => mapImage(img, result.article_id))
  }

  async uploadImage(articleId: string, imageData: Uint8Array | ArrayBuffer, filename: string, options?: import('@/types/api').ImageUploadOptions): Promise<ImageInfo> {
    const bytes = imageData instanceof ArrayBuffer ? new Uint8Array(imageData) : imageData
    const formData = new FormData()
    const buf = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer
    formData.append('file', new Blob([buf], { type: options?.mimeType || inferImageMimeType(filename) }), filename)
    if (options?.slug) formData.append('slug', options.slug)
    if (options?.alt) formData.append('alt', options.alt)
    const image = await this.request<ImageDTO>({
      method: 'POST',
      url: apiPath(`/articles/${encodeURIComponent(articleId)}/images`),
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    this.imageArticleMap.set(image.relative_path, { articleId, imageName: image.name })
    return mapImage(image, articleId)
  }

  async deleteImage(path: string, _sha?: string, options?: import('@/types/api').MutationOptions) {
    const cached = this.imageArticleMap.get(path)
    if (!cached) throw createAPIError(ErrorCode.VALIDATION_ERROR, '缺少图片所属文章信息')
    return this.request({
      method: 'DELETE',
      url: apiPath(`/articles/${encodeURIComponent(cached.articleId)}/images/${encodeURIComponent(cached.imageName)}`),
      params: mutationParams(options)
    })
  }

  async scanUnusedImages(articleId: string) {
    const check = await this.request<{ unused_images: string[]; missing_references: string[]; out_of_scope_references: string[] }>({
      method: 'POST',
      url: apiPath(`/articles/${encodeURIComponent(articleId)}/images/check`)
    })
    const images = await this.getImages(articleId)
    const unused = new Set(check.unused_images)
    return {
      unusedImages: images.filter((img) => unused.has(img.name)),
      count: check.unused_images.length,
      missingReferences: check.missing_references,
      outOfScopeReferences: check.out_of_scope_references
    }
  }

  async cleanupUnusedImages(articleId: string) {
    const result = await this.scanUnusedImages(articleId)
    for (const img of result.unusedImages || []) await this.deleteImage(img.path)
    return { ...result, deleted: result.unusedImages, count: result.unusedImages.length, unusedImages: [] }
  }

  async getImageFolders(): Promise<ImageFolderInfo[]> {
    const posts = await this.getPosts()
    const folders = await Promise.all(posts.map(async (post) => {
      try {
        const images = await this.getImages(post.path)
        if (images.length === 0) return null
        return {
          folderPath: images[0]?.path.split('/').slice(0, -1).join('/') || post.relativePath || post.path,
          articlePath: post.path,
          articleExists: true,
          imageCount: images.length,
          images
        }
      } catch {
        return null
      }
    }))
    return folders.filter(Boolean) as ImageFolderInfo[]
  }

  async getCategories(params?: { type?: ArticleType; includeEmpty?: boolean; includeCounts?: boolean }): Promise<CategoryDTO[]> {
    return this.request<CategoryDTO[]>({
      method: 'GET',
      url: apiPath('/categories'),
      params: { type: params?.type, include_empty: params?.includeEmpty, include_counts: params?.includeCounts }
    })
  }

  async createCategory(payload: import('@/types/api').CategoryCreateDTO): Promise<CategoryDTO> {
    return this.request<CategoryDTO>({ method: 'POST', url: apiPath('/categories'), data: payload })
  }

  async getTags(params?: { keyword?: string; page?: number; pageSize?: number; sort?: string }) {
    const result = await this.request<unknown>({
      method: 'GET',
      url: apiPath('/tags'),
      params: { keyword: params?.keyword, page: params?.page, page_size: params?.pageSize, sort: params?.sort }
    })
    return Array.isArray(result) ? result : (result as { items: [] }).items
  }

  async createTag(payload: import('@/types/api').TagCreateDTO): Promise<TagDTO> {
    return this.request<TagDTO>({ method: 'POST', url: apiPath('/tags'), data: payload })
  }

  async getGitStatus(includeUntracked = true): Promise<GitStatusDTO> {
    return this.request<GitStatusDTO>({ method: 'GET', url: apiPath('/git/status'), params: { include_untracked: includeUntracked } })
  }

  async commit(message: string, options?: import('@/types/api').MutationOptions & { paths?: string[] }) {
    return this.request({
      method: 'POST',
      url: apiPath('/git/commit'),
      data: { message, paths: options?.paths || [], ...mutationParams(options) }
    })
  }

  async push(options?: import('@/types/api').MutationOptions & { remote?: string; branch?: string | null }) {
    return this.request({
      method: 'POST',
      url: apiPath('/git/push'),
      data: { remote: options?.remote || 'origin', branch: options?.branch ?? null, ...mutationParams(options) }
    })
  }

  async deploy(message: string, _filePath?: string, options?: import('@/types/api').DeployOptions) {
    return this.request({
      method: 'POST',
      url: apiPath('/deploy'),
      data: { branch: options?.branch || 'develop', run_build_first: options?.runBuildFirst ?? true, clean_build: options?.cleanBuild ?? false, stage_mode: options?.stageMode || 'site', paths: options?.paths || ['site'], allow_rebase: options?.allowRebase ?? true, commit_message: message, ...mutationParams(options) },
      timeout: 900000
    })
  }

  async runBuild(clean = false): Promise<TaskDTO> {
    return this.request<TaskDTO>({ method: 'POST', url: apiPath('/build'), data: { command: 'build', clean } })
  }

  async getBuildTask(taskId: string): Promise<TaskDTO> {
    return this.request<TaskDTO>({ method: 'GET', url: apiPath(`/build/tasks/${encodeURIComponent(taskId)}`) })
  }

  async startPreview(options?: { port?: number; host?: string; openBrowser?: boolean }): Promise<PreviewStatusDTO> {
    return this.request<PreviewStatusDTO>({ method: 'POST', url: apiPath('/preview/start'), data: { port: options?.port ?? 3000, host: options?.host || '127.0.0.1', open_browser: options?.openBrowser ?? false } })
  }

  async getPreviewStatus(): Promise<PreviewStatusDTO> {
    return this.request<PreviewStatusDTO>({ method: 'GET', url: apiPath('/preview/status') })
  }

  async validateArticle(articleId: string): Promise<{ article_id: string; issues: ValidationIssue[] }> {
    return this.request<{ article_id: string; issues: ValidationIssue[] }>({ method: 'POST', url: apiPath(`/articles/${encodeURIComponent(articleId)}/validate`) })
  }

  async validateSite(options?: { includeImages?: boolean; includeLinks?: boolean; includeSidebars?: boolean; type?: ArticleType | null }): Promise<SiteValidationResultDTO> {
    return this.request<SiteValidationResultDTO>({ method: 'POST', url: apiPath('/validation/site'), data: { include_images: options?.includeImages ?? true, include_links: options?.includeLinks ?? true, include_sidebars: options?.includeSidebars ?? true, type: options?.type ?? null } })
  }

  async syncSidebars(options?: import('@/types/api').MutationOptions & { mode?: string }) {
    return this.request({ method: 'POST', url: apiPath('/sidebars/sync'), data: { mode: options?.mode || 'append_missing', ...mutationParams(options) } })
  }

  async syncBackendIndex(options?: import('@/types/api').MutationOptions) {
    return this.request({ method: 'POST', url: apiPath('/sync/backend-index'), data: mutationParams(options) })
  }

  async syncSiteConfig(options?: import('@/types/api').MutationOptions) {
    return this.request({ method: 'POST', url: apiPath('/sync/site-config'), data: mutationParams(options) })
  }

  async getDocusaurusConfigStatus(): Promise<DocusaurusConfigStatusDTO> {
    return this.request<DocusaurusConfigStatusDTO>({ method: 'GET', url: apiPath('/docusaurus-config/status') })
  }

  async syncDocusaurusConfig(options?: import('@/types/api').MutationOptions & { mode?: string }) {
    return this.request({ method: 'POST', url: apiPath('/docusaurus-config/sync'), data: { mode: options?.mode || 'all', ...mutationParams(options) } })
  }

  async getSchema(): Promise<ContentSchemaDTO> {
    return this.request<ContentSchemaDTO>({ method: 'GET', url: apiPath('/schema') })
  }

  async initSchema(options?: import('@/types/api').MutationOptions & { overwrite?: boolean }) {
    return this.request({ method: 'POST', url: apiPath('/schema/init'), data: { overwrite: options?.overwrite ?? false, ...mutationParams(options) } })
  }

  async syncTags(options?: import('@/types/api').MutationOptions) {
    return this.request({ method: 'POST', url: apiPath('/tags/sync'), params: mutationParams(options) })
  }

  async renameCategory(categoryId: string, options: import('@/types/api').CategoryRenameOptions) {
    return this.request({ method: 'POST', url: apiPath(`/categories/${encodeURIComponent(categoryId)}/rename`), data: { target_slug: options.targetSlug, target_label: options.targetLabel ?? null, replace_links: options.replaceLinks ?? true, ...mutationParams(options) } })
  }

  async deleteCategory(categoryId: string, options?: import('@/types/api').CategoryDeleteOptions) {
    return this.request({ method: 'DELETE', url: apiPath(`/categories/${encodeURIComponent(categoryId)}`), params: mutationParams(options) })
  }

  async getSidebarStatus(includeDetails = true): Promise<SidebarStatusDTO> {
    return this.request<SidebarStatusDTO>({ method: 'GET', url: apiPath('/sidebars/status'), params: { include_details: includeDetails } })
  }

  async rebuildRegistryIndex(): Promise<RegistryIndexSyncResultDTO> {
    return this.request<RegistryIndexSyncResultDTO>({ method: 'POST', url: apiPath('/registry-index/sync') })
  }

  async getRegistryIndexStats(): Promise<RegistryIndexStatsDTO> {
    return this.request<RegistryIndexStatsDTO>({ method: 'GET', url: apiPath('/registry-index/stats') })
  }

  async getRegistryEntities(params?: import('@/types/api').RegistryIndexQueryParams): Promise<RegistryIndexListResponseDTO> {
    return this.request<RegistryIndexListResponseDTO>({ method: 'GET', url: apiPath('/registry-index/entities'), params: { entity_type: params?.entityType, q: params?.q, status: params?.status || 'active', page: params?.page || 1, page_size: params?.pageSize || 20, sort: params?.sort || 'updated_at', order: params?.order || 'desc' } })
  }

  async getRegistryYaml(registryType: string): Promise<RegistryYamlFileDTO> {
    return this.request<RegistryYamlFileDTO>({ method: 'GET', url: apiPath(`/registry-index/yaml/${encodeURIComponent(registryType)}`) })
  }

  async saveRegistryYaml(registryType: string, payload: import('@/types/api').RegistryYamlSaveDTO) {
    return this.request({ method: 'PUT', url: apiPath(`/registry-index/yaml/${encodeURIComponent(registryType)}`), data: payload })
  }

  async getRegistryYamlEntries(registryType: string): Promise<RegistryYamlEntriesDTO> {
    return this.request<RegistryYamlEntriesDTO>({ method: 'GET', url: apiPath(`/registry-index/yaml/${encodeURIComponent(registryType)}/entries`) })
  }

  async saveRegistryYamlEntries(registryType: string, payload: import('@/types/api').RegistryYamlEntriesSaveDTO) {
    return this.request({ method: 'PUT', url: apiPath(`/registry-index/yaml/${encodeURIComponent(registryType)}/entries`), data: payload })
  }

  async getRegistryDiff(registryType: string): Promise<RegistryDiffDTO> {
    return this.request<RegistryDiffDTO>({ method: 'GET', url: apiPath(`/registry-index/diff/${encodeURIComponent(registryType)}`) })
  }

  async searchArticles(params: { q: string; type?: ArticleType; limit?: number; offset?: number }): Promise<SearchResultDTO> {
    return this.request<SearchResultDTO>({ method: 'GET', url: apiPath('/search'), params: { q: params.q, type: params.type, limit: params.limit, offset: params.offset } })
  }

  async rebuildSearchIndex(options?: { type?: ArticleType | null; force?: boolean }): Promise<SearchIndexResultDTO> {
    return this.request<SearchIndexResultDTO>({ method: 'POST', url: apiPath('/search/index'), data: { type: options?.type ?? null, force: options?.force ?? false } })
  }

  async getAIModels(): Promise<AIModelConfigDTO[]> {
    return this.request<AIModelConfigDTO[]>({ method: 'GET', url: apiPath('/ai/models') })
  }

  async saveAIModel(model: import('@/types/api').AIModelConfigDTO & { apiKey?: string }): Promise<AIModelConfigDTO> {
    return this.request<AIModelConfigDTO>({ method: 'PUT', url: apiPath(`/ai/models/${encodeURIComponent(model.id)}`), data: model })
  }

  async deleteAIModel(modelId: string): Promise<AIModelConfigDTO[]> {
    return this.request<AIModelConfigDTO[]>({ method: 'DELETE', url: apiPath(`/ai/models/${encodeURIComponent(modelId)}`) })
  }

  async testAIModel(modelId: string): Promise<AIModelTestResultDTO> {
    return this.request<AIModelTestResultDTO>({ method: 'POST', url: apiPath(`/ai/models/${encodeURIComponent(modelId)}/test`) })
  }

  async createAIDraft(payload: import('@/types/api').AIDraftRequestDTO): Promise<AIDraftResultDTO> {
    return this.request<AIDraftResultDTO>({ method: 'POST', url: apiPath('/ai/draft'), data: payload })
  }

  async rewriteAIContent(payload: import('@/types/api').AIRewriteRequestDTO): Promise<AIRewriteResultDTO> {
    return this.request<AIRewriteResultDTO>({ method: 'POST', url: apiPath('/ai/rewrite'), data: payload })
  }

  async getGitSyncStatus(): Promise<GitSyncStatusDTO> {
    return this.request<GitSyncStatusDTO>({ method: 'GET', url: apiPath('/git-sync/status') })
  }

  async createGitSshKey(options?: { email?: string; overwrite?: boolean }): Promise<GitCommandResultDTO> {
    return this.request<GitCommandResultDTO>({ method: 'POST', url: apiPath('/git-sync/ssh-key'), data: { email: options?.email || null, overwrite: options?.overwrite ?? false } })
  }

  async updateGitRemote(remoteUrl: string): Promise<GitCommandResultDTO> {
    return this.request<GitCommandResultDTO>({ method: 'POST', url: apiPath('/git-sync/remote'), data: { remote_url: remoteUrl } })
  }

  async testGitSsh(): Promise<GitCommandResultDTO> {
    return this.request<GitCommandResultDTO>({ method: 'POST', url: apiPath('/git-sync/ssh-test') })
  }

  async pullFromGitHub(options?: import('@/types/api').GitPullOptions): Promise<GitCommandResultDTO> {
    return this.request<GitCommandResultDTO>({ method: 'POST', url: apiPath('/git-sync/pull'), data: { branch: options?.branch || 'develop', mode: options?.mode || 'ff_only', run_build_after: options?.runBuildAfter ?? false }, timeout: 900000 })
  }

  async fetchWebMaterial(payload: import('@/types/api').FetchWebRequestDTO): Promise<FetchWebResultDTO> {
    return this.request<FetchWebResultDTO>({ method: 'POST', url: apiPath('/fetch/web'), data: payload })
  }
}

// 单例导出
export const api = new DesktopAPIClient() as unknown as BlogAPI

export function getAPI(): BlogAPI {
  return api
}

export async function checkAPIAvailable(): Promise<boolean> {
  try {
    return await api.checkHealth()
  } catch {
    return false
  }
}

export type { LocalAPIError, RetryConfig }
export { ErrorCode as LocalAPIErrorCode, createAPIError }
