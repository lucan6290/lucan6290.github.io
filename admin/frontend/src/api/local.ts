import axios, { AxiosError } from 'axios'
import type { AxiosInstance, AxiosRequestConfig } from 'axios'
import type {
  AIDraftRequestDTO,
  AIDraftResultDTO,
  AIRewriteRequestDTO,
  AIRewriteResultDTO,
  ArticleDeleteOptions,
  ArticleCreateOptions,
  ArticleMoveOptions,
  AssetCleanupResult,
  CategoryCreateDTO,
  CategoryDTO,
  ContentSchemaDTO,
  FetchWebRequestDTO,
  FetchWebResultDTO,
  GitOperationResult,
  GitStatusDTO,
  GitCommitResultDTO,
  GitPushResultDTO,
  ImageUploadOptions,
  ImageFolderInfo,
  ImageInfo,
  MutationOptions,
  PostDetail,
  PostInfo,
  PreviewStatusDTO,
  RegistryIndexListResponseDTO,
  RegistryIndexQueryParams,
  RegistryIndexStatsDTO,
  RegistryIndexSyncResultDTO,
  RegistryDiffDTO,
  RegistryYamlEntriesDTO,
  RegistryYamlEntriesSaveDTO,
  RegistryYamlFileDTO,
  RegistryYamlSaveDTO,
  SchemaInitResultDTO,
  SearchIndexResultDTO,
  SearchResultDTO,
  SidebarStatusDTO,
  SiteValidationResultDTO,
  TagCreateDTO,
  TagDTO,
  TagSyncResultDTO
} from '@/types/api'
import type {
  AgentCommitRequest,
  AgentCommitResponse,
  AgentPlanRequest,
  AgentPlanResponse,
  AIDraftPlan,
  ArticleIndexScanResult,
  ArticleIndexSummary,
  CategoryRegistryItem,
  KnowledgeQARequest,
  KnowledgeQAResponse
} from '@/types/ai-writing'
import type {
  LocalAPIError,
  LocalAPIErrorCode,
  RetryConfig
} from '@/types/local'
import { resolveIssueStatus } from '@/utils/postDisplay'
import { LocalAPIErrorCode as ErrorCode } from '@/types/local'
import { parseFrontMatter, stripLeadingBom } from '@/utils/frontmatter'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:18000'
const API_PREFIX = '/api/v1'

const LOCAL_API_CONFIG = {
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  retryDelay: 1000,
  backoffFactor: 2
}

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

interface ArticleImageCheckDTO {
  article_id: string
  image_dir: string | null
  referenced_images: string[]
  unused_images: string[]
  missing_references: string[]
  out_of_scope_references: string[]
}

interface MutationPlanDTO {
  dry_run: boolean
  requires_confirmation: boolean
  changes: Array<{
    action: string
    target: string
    from?: string | null
    to?: string | null
    description: string
  }>
  warnings: string[]
}

interface TaskDTO {
  task_id: string
  type: string
  status: string
  started_at?: string | null
  finished_at?: string | null
  exit_code?: number | null
  logs?: string
  error?: Record<string, unknown> | null
}

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

function stringifyDetails(details: unknown): string | undefined {
  if (details === undefined || details === null) return undefined
  if (typeof details === 'string') return details
  try {
    return JSON.stringify(details)
  } catch {
    return String(details)
  }
}

function apiPath(path: string): string {
  return `${API_PREFIX}${path}`
}

function extractErrorFromAxios(error: AxiosError): LocalAPIError {
  if (!error.response) {
    return createAPIError(
      ErrorCode.NETWORK_ERROR,
      '网络连接失败',
      `无法连接到管理员后端服务，请确保服务已启动（${API_BASE_URL}）`,
      error
    )
  }

  const status = error.response.status
  const data = error.response.data as {
    code?: string
    message?: string
    request_id?: string | null
    details?: unknown
  }
  const message = data?.message || `请求失败 (${status})`
  const details = stringifyDetails(data?.details)
  const knownCode =
    status === 404 ? ErrorCode.FILE_NOT_FOUND :
    status === 403 ? ErrorCode.PERMISSION_DENIED :
    status === 400 || status === 409 || status === 422 || status === 428 ? ErrorCode.VALIDATION_ERROR :
    status >= 500 ? ErrorCode.SERVER_ERROR :
    ErrorCode.UNKNOWN_ERROR

  return createAPIError(knownCode, message, details, error)
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

async function executeWithRetry<T>(
  requestFn: () => Promise<T>,
  config: RetryConfig = DEFAULT_RETRY_CONFIG
): Promise<T> {
  let lastError: unknown = null
  let currentDelay = config.retryDelay

  for (let attempt = 1; attempt <= config.maxRetries; attempt++) {
    try {
      return await requestFn()
    } catch (error) {
      lastError = error

      const apiError = axios.isAxiosError(error) ? extractErrorFromAxios(error) : error as LocalAPIError
      const retryable = apiError.code === ErrorCode.NETWORK_ERROR || apiError.code === ErrorCode.SERVER_ERROR
      if (!retryable || attempt === config.maxRetries) {
        throw apiError
      }

      console.warn(`请求失败，第 ${attempt} 次重试...`, {
        error: apiError.message,
        nextRetryIn: currentDelay
      })
      await delay(currentDelay)
      currentDelay *= config.backoffFactor || 2
    }
  }

  throw lastError
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

function categoryLabelKey(type: string, path: string[]): string {
  return `${type}:${path.join('/')}`
}

function buildCategoryLabelMap(categories: CategoryDTO[]): Map<string, string> {
  const labels = new Map<string, string>()
  for (const category of flattenCategoryTree(categories)) {
    labels.set(categoryLabelKey(category.type, category.path), category.label || category.slug)
  }
  return labels
}

function mapCategoryLabels(article: ArticleSummaryDTO, categoryLabelMap?: Map<string, string>): string[] {
  const categoryPath = article.category_path || []
  if (!categoryPath.length) {
    return article.category_label ? [article.category_label] : []
  }

  return categoryPath.map((_, index) => {
    const currentPath = categoryPath.slice(0, index + 1)
    const mappedLabel = categoryLabelMap?.get(categoryLabelKey(article.type, currentPath))
    if (mappedLabel) return mappedLabel
    if (index === categoryPath.length - 1 && article.category_label) return article.category_label
    return currentPath[currentPath.length - 1]
  })
}

function mapSummaryToPost(article: ArticleSummaryDTO, categoryLabelMap?: Map<string, string>): PostInfo {
  const categoryPath = article.category_path || []
  const category = categoryPath[0] || article.type
  const subCategory = categoryPath[1] || ''
  const categoryLabels = mapCategoryLabels(article, categoryLabelMap)
  const issues = article.issues || []
  const displayStatus = resolveIssueStatus(issues)

  return {
    id: article.id,
    type: article.type,
    typeLabel: article.type_label || (article.type === 'blog' ? '博客' : article.type === 'docs' ? '知识库' : article.type),
    filename: basenameWithoutExt(article.relative_path),
    path: article.id,
    fullPath: article.relative_path,
    sha: article.version,
    version: article.version,
    route: article.route,
    relativePath: article.relative_path,
    slug: article.slug,
    title: article.title || basenameWithoutExt(article.relative_path),
    category,
    subCategory,
    categories: categoryLabels.length > 0 ? categoryLabels : [article.category_label || article.type],
    tags: article.tags || [],
    authors: article.authors || [],
    date: article.updated_at,
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

function mapDetailToPost(article: ArticleDetailDTO, categoryLabelMap?: Map<string, string>): PostDetail {
  const summary = mapSummaryToPost(article, categoryLabelMap)
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

function sanitizePathSegment(value: string): string {
  const segment = value
    .trim()
    .replace(/\.[^.]+$/, '')
    .replace(/[<>:"\\|?*\x00-\x1f/]+/g, '-')
    .replace(/\s+/g, '-')
    .replace(/-{2,}/g, '-')
    .replace(/^[.\s-]+|[.\s-]+$/g, '')
  return segment || `article-${Date.now()}`
}

function splitCsv(value: string | undefined): string[] {
  if (!value) return []
  return value.split(/[,，]/).map(item => item.trim()).filter(Boolean)
}

function inferImageMimeType(filename: string): string {
  const extension = filename.match(/\.[^.]+$/)?.[0]?.toLowerCase()
  const mimeTypes: Record<string, string> = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.webp': 'image/webp',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml'
  }
  return mimeTypes[extension || ''] || 'application/octet-stream'
}

function flattenCategoryTree(categories: CategoryDTO[]): CategoryDTO[] {
  const items: CategoryDTO[] = []
  const visit = (category: CategoryDTO) => {
    items.push(category)
    ;(category.children || []).forEach(visit)
  }
  categories.forEach(visit)
  return items
}

function categoryCompletenessScore(category: CategoryDTO): number {
  return [
    category.label,
    category.description,
    category.cover,
    category.sort_order,
    category.children?.length
  ].filter((value) => value !== undefined && value !== null && value !== '').length
}

function mapCategoryTreeToRegistry(categories: CategoryDTO[]): CategoryRegistryItem[] {
  const byPath = new Map<string, CategoryDTO>()

  for (const category of flattenCategoryTree(categories)) {
    if (!category.path.length) continue
    const key = `${category.type}:${category.path.join('/')}`
    const existing = byPath.get(key)
    if (!existing || categoryCompletenessScore(category) > categoryCompletenessScore(existing)) {
      byPath.set(key, category)
    }
  }

  const nodes = [...byPath.values()]
  const roots = nodes
    .filter((category) => category.path.length === 1)
    .sort((a, b) => (a.sort_order ?? 9999) - (b.sort_order ?? 9999) || a.path.join('/').localeCompare(b.path.join('/')))

  return roots.map((category, index) => {
    const children = nodes
      .filter((child) =>
        child.type === category.type &&
        child.path.length === 2 &&
        child.path[0] === category.path[0]
      )
      .sort((a, b) => (a.sort_order ?? 9999) - (b.sort_order ?? 9999) || a.path.join('/').localeCompare(b.path.join('/')))

    return {
      type: category.type,
      frontend_name1: category.label || category.slug,
      category_slug: category.path[0] || category.slug,
      note_prefix1: category.path[0] || category.slug,
      cover: category.cover || '',
      sort_order: category.sort_order ?? (index + 1) * 10,
      enabled: category.enabled !== false,
      children: children.map((child, childIndex) => ({
        frontend_name2: child.label || child.slug,
        note_prefix2: child.path[1] || child.slug,
        sort_order: child.sort_order ?? (childIndex + 1) * 10,
        enabled: child.enabled !== false
      })),
      prefix1: category.path[0] || category.slug,
      primaryName: category.label || category.slug,
      primarySlug: category.path[0] || category.slug,
      dir: category.path.join('/')
    }
  })
}

function isMutationPlan(value: unknown): value is MutationPlanDTO {
  return (
    typeof value === 'object' &&
    value !== null &&
    'requires_confirmation' in value &&
    typeof (value as MutationPlanDTO).requires_confirmation === 'boolean'
  )
}

function mutationParams(options?: MutationOptions): { dry_run: boolean; confirm: boolean } {
  return {
    dry_run: options?.dryRun ?? false,
    confirm: options?.confirm ?? true
  }
}

function mutationBody(options?: MutationOptions): { dry_run: boolean; confirm: boolean } {
  return mutationParams(options)
}

class LocalAPIClient {
  private client: AxiosInstance
  private retryConfig: RetryConfig
  private loadedVersions = new Map<string, string>()
  private imageArticleMap = new Map<string, { articleId: string; imageName: string }>()

  constructor() {
    this.client = axios.create(LOCAL_API_CONFIG)
    this.retryConfig = DEFAULT_RETRY_CONFIG

    this.client.interceptors.response.use(
      response => response,
      (error: AxiosError | LocalAPIError) => {
        if (axios.isAxiosError(error)) {
          return Promise.reject(extractErrorFromAxios(error))
        }
        return Promise.reject(error)
      }
    )
  }

  private async request<T>(config: AxiosRequestConfig): Promise<T> {
    return executeWithRetry(
      () => this.client.request<T>(config).then(res => res.data),
      this.retryConfig
    )
  }

  private async getCategoryLabelMap(): Promise<Map<string, string>> {
    const categories = await this.getCategories({
      includeEmpty: true,
      includeCounts: false
    })
    return buildCategoryLabelMap(categories)
  }

  async getPosts(): Promise<PostInfo[]> {
    const [firstPage, categoryLabelMap] = await Promise.all([
      this.request<ArticleListResponseDTO>({
        method: 'GET',
        url: apiPath('/articles'),
        params: {
          page: 1,
          page_size: 100,
          sort: '-updated_at'
        }
      }),
      this.getCategoryLabelMap().catch(() => new Map<string, string>())
    ])

    const items = [...firstPage.items]
    let page = firstPage.page
    while (firstPage.has_next && items.length < firstPage.total) {
      page += 1
      const nextPage = await this.request<ArticleListResponseDTO>({
        method: 'GET',
        url: apiPath('/articles'),
        params: {
          page,
          page_size: firstPage.page_size,
          sort: '-updated_at'
        }
      })
      items.push(...nextPage.items)
      if (!nextPage.has_next) break
    }

    return items.map((item) => mapSummaryToPost(item, categoryLabelMap))
  }

  async getPost(articleId: string): Promise<PostDetail> {
    const [detail, categoryLabelMap] = await Promise.all([
      this.request<ArticleDetailDTO>({
        method: 'GET',
        url: apiPath(`/articles/${encodeURIComponent(articleId)}`)
      }),
      this.getCategoryLabelMap().catch(() => new Map<string, string>())
    ])
    this.loadedVersions.set(articleId, detail.version)
    return mapDetailToPost(detail, categoryLabelMap)
  }

  async createPost(path: string, content: string, options?: ArticleCreateOptions & { prefix1?: string; prefix2?: string }): Promise<PostDetail> {
    const fallbackSlug = path ? basenameWithoutExt(path) : options?.title || 'untitled'
    const type = options?.type || 'docs'
    const categoryPath = options?.categoryPath || path.split('/').slice(0, -1).map(sanitizePathSegment).filter(Boolean)
    const tags = options?.tags || splitCsv(options?.prefix2)
    const authors = options?.authors || ['lucan']

    const detail = await this.request<ArticleDetailDTO>({
      method: 'POST',
      url: apiPath('/articles'),
      data: {
        type,
        title: options?.title || fallbackSlug,
        slug: sanitizePathSegment(options?.slug || fallbackSlug),
        description: options?.description || null,
        body: content || '',
        category_path: type === 'docs' ? categoryPath : [],
        sidebar_position: options?.sidebarPosition ?? null,
        authors: type === 'blog' ? authors : [],
        tags: type === 'blog' ? tags.length ? tags : ['note'] : [],
        date: type === 'blog' ? options?.date || null : null
      }
    })
    this.loadedVersions.set(detail.id, detail.version)
    const categoryLabelMap = await this.getCategoryLabelMap().catch(() => new Map<string, string>())
    return mapDetailToPost(detail, categoryLabelMap)
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
    const categoryLabelMap = await this.getCategoryLabelMap().catch(() => new Map<string, string>())
    return mapDetailToPost(detail, categoryLabelMap)
  }

  async deletePost(articleId: string, _sha?: string, options?: ArticleDeleteOptions): Promise<void | MutationPlanDTO> {
    const result = await this.request<MutationPlanDTO>({
      method: 'DELETE',
      url: apiPath(`/articles/${encodeURIComponent(articleId)}`),
      params: {
        with_images: options?.withImages ?? false,
        ...mutationParams(options)
      }
    })
    if (options?.dryRun) return result
  }

  async movePost(articleId: string, options: ArticleMoveOptions): Promise<MutationPlanDTO> {
    return this.request<MutationPlanDTO>({
      method: 'POST',
      url: apiPath(`/articles/${encodeURIComponent(articleId)}/move`),
      data: {
        target_type: options.targetType,
        target_slug: options.targetSlug,
        target_category_path: options.targetCategoryPath || [],
        target_date: options.targetDate ?? null,
        replace_links: options.replaceLinks ?? false,
        ...mutationBody(options)
      }
    })
  }

  async uploadImage(articleId: string, imageData: Uint8Array | ArrayBuffer, filename: string, options?: ImageUploadOptions): Promise<ImageInfo> {
    const fileBytes = imageData instanceof ArrayBuffer ? new Uint8Array(imageData) : imageData
    const formData = new FormData()
    const fileBuffer = fileBytes.buffer.slice(fileBytes.byteOffset, fileBytes.byteOffset + fileBytes.byteLength) as ArrayBuffer
    formData.append('file', new Blob([fileBuffer], { type: options?.mimeType || inferImageMimeType(filename) }), filename)
    if (options?.slug) formData.append('slug', options.slug)
    if (options?.alt) formData.append('alt', options.alt)

    const image = await this.request<ImageDTO>({
      method: 'POST',
      url: apiPath(`/articles/${encodeURIComponent(articleId)}/images`),
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    this.imageArticleMap.set(image.relative_path, { articleId, imageName: image.name })
    return mapImage(image, articleId)
  }

  async getImages(articleId: string): Promise<ImageInfo[]> {
    const result = await this.request<ArticleImageListDTO>({
      method: 'GET',
      url: apiPath(`/articles/${encodeURIComponent(articleId)}/images`)
    })

    for (const image of result.images) {
      this.imageArticleMap.set(image.relative_path, { articleId: result.article_id, imageName: image.name })
    }

    return result.images.map(image => mapImage(image, result.article_id))
  }

  async getImageFolders(): Promise<ImageFolderInfo[]> {
    const posts = await this.getPosts()
    const folders = await Promise.all(posts.map(async (post) => {
      try {
        const images = await this.getImages(post.path)
        if (images.length === 0) return null
        const folderPath = images[0]?.path.split('/').slice(0, -1).join('/') || post.relativePath || post.path
        return {
          folderPath,
          articlePath: post.path,
          articleExists: true as boolean,
          imageCount: images.length,
          images
        }
      } catch {
        return null
      }
    }))

    return folders.filter(Boolean) as ImageFolderInfo[]
  }

  async scanUnusedImages(articleId: string): Promise<AssetCleanupResult> {
    const check = await this.request<ArticleImageCheckDTO>({
      method: 'POST',
      url: apiPath(`/articles/${encodeURIComponent(articleId)}/images/check`)
    })
    const images = await this.getImages(articleId)
    const unusedNames = new Set(check.unused_images)
    return {
      unusedImages: images.filter(image => unusedNames.has(image.name)),
      count: check.unused_images.length,
      missingReferences: check.missing_references,
      outOfScopeReferences: check.out_of_scope_references
    }
  }

  async cleanupUnusedImages(articleId: string): Promise<AssetCleanupResult> {
    const result = await this.scanUnusedImages(articleId)
    const deleted: ImageInfo[] = []

    for (const image of result.unusedImages || []) {
      await this.deleteImage(image.path)
      deleted.push(image)
    }

    return {
      ...result,
      deleted,
      count: deleted.length,
      unusedImages: []
    }
  }

  async deleteImage(path: string, _sha?: string, options?: MutationOptions): Promise<void | MutationPlanDTO> {
    const cached = this.imageArticleMap.get(path)
    if (!cached) {
      throw createAPIError(ErrorCode.VALIDATION_ERROR, '缺少图片所属文章信息，请刷新图片列表后重试。')
    }

    const result = await this.request<MutationPlanDTO>({
      method: 'DELETE',
      url: apiPath(`/articles/${encodeURIComponent(cached.articleId)}/images/${encodeURIComponent(cached.imageName)}`),
      params: mutationParams(options)
    })
    if (options?.dryRun) return result
  }

  async validateArticle(articleId: string): Promise<{ article_id: string; issues: ValidationIssueDTO[] }> {
    return this.request({
      method: 'POST',
      url: apiPath(`/articles/${encodeURIComponent(articleId)}/validate`)
    })
  }

  async getCategories(params?: { type?: ArticleType; includeEmpty?: boolean; includeCounts?: boolean }): Promise<CategoryDTO[]> {
    return this.request<CategoryDTO[]>({
      method: 'GET',
      url: apiPath('/categories'),
      params: {
        type: params?.type,
        include_empty: params?.includeEmpty,
        include_counts: params?.includeCounts
      }
    })
  }

  async createCategory(payload: CategoryCreateDTO): Promise<CategoryDTO> {
    return this.request<CategoryDTO>({
      method: 'POST',
      url: apiPath('/categories'),
      data: payload
    })
  }

  async getCategoryRegistry(): Promise<CategoryRegistryItem[]> {
    const categories = await this.getCategories({
      includeEmpty: true,
      includeCounts: false
    })
    return mapCategoryTreeToRegistry(categories)
  }

  async getTags(params?: { keyword?: string; page?: number; pageSize?: number; sort?: string }): Promise<TagDTO[]> {
    const result = await this.request<TagDTO[] | { items: TagDTO[] }>({
      method: 'GET',
      url: apiPath('/tags'),
      params: {
        keyword: params?.keyword || undefined,
        page: params?.page,
        page_size: params?.pageSize,
        sort: params?.sort
      }
    })
    return Array.isArray(result) ? result : result.items
  }

  async createTag(payload: TagCreateDTO): Promise<TagDTO> {
    return this.request<TagDTO>({
      method: 'POST',
      url: apiPath('/tags'),
      data: payload
    })
  }

  async syncTags(options?: MutationOptions): Promise<TagSyncResultDTO> {
    return this.request<TagSyncResultDTO>({
      method: 'POST',
      url: apiPath('/tags/sync'),
      params: {
        dry_run: options?.dryRun ?? false,
        confirm: options?.confirm ?? true
      }
    })
  }

  async getSidebarStatus(includeDetails = true): Promise<SidebarStatusDTO> {
    return this.request<SidebarStatusDTO>({
      method: 'GET',
      url: apiPath('/sidebars/status'),
      params: {
        include_details: includeDetails
      }
    })
  }

  async syncSidebars(options?: MutationOptions & { mode?: 'append_missing' | 'regenerate' | string }): Promise<MutationPlanDTO> {
    return this.request<MutationPlanDTO>({
      method: 'POST',
      url: apiPath('/sidebars/sync'),
      data: {
        mode: options?.mode || 'append_missing',
        ...mutationBody(options)
      }
    })
  }

  async validateSite(options?: { includeImages?: boolean; includeLinks?: boolean; includeSidebars?: boolean; type?: ArticleType | null }): Promise<SiteValidationResultDTO> {
    return this.request<SiteValidationResultDTO>({
      method: 'POST',
      url: apiPath('/validation/site'),
      data: {
        include_images: options?.includeImages ?? true,
        include_links: options?.includeLinks ?? true,
        include_sidebars: options?.includeSidebars ?? true,
        type: options?.type ?? null
      }
    })
  }

  async runBuild(clean = false): Promise<TaskDTO> {
    return this.request<TaskDTO>({
      method: 'POST',
      url: apiPath('/build'),
      data: {
        command: 'build',
        clean
      }
    })
  }

  async getBuildTask(taskId: string): Promise<TaskDTO> {
    return this.request<TaskDTO>({
      method: 'GET',
      url: apiPath(`/build/tasks/${encodeURIComponent(taskId)}`)
    })
  }

  async startPreview(options?: { port?: number; host?: string; openBrowser?: boolean }): Promise<PreviewStatusDTO> {
    return this.request<PreviewStatusDTO>({
      method: 'POST',
      url: apiPath('/preview/start'),
      data: {
        port: options?.port ?? 3000,
        host: options?.host || '127.0.0.1',
        open_browser: options?.openBrowser ?? false
      }
    })
  }

  async getPreviewStatus(): Promise<PreviewStatusDTO> {
    return this.request<PreviewStatusDTO>({
      method: 'GET',
      url: apiPath('/preview/status')
    })
  }

  async getGitStatus(includeUntracked = true): Promise<GitStatusDTO> {
    return this.request<GitStatusDTO>({
      method: 'GET',
      url: apiPath('/git/status'),
      params: {
        include_untracked: includeUntracked
      }
    })
  }

  async commit(message: string, options?: MutationOptions & { paths?: string[] }): Promise<GitOperationResult | MutationPlanDTO | GitCommitResultDTO> {
    const result = await this.request<MutationPlanDTO | GitCommitResultDTO | { status?: string; commit?: string }>({
      method: 'POST',
      url: apiPath('/git/commit'),
      data: {
        message,
        paths: options?.paths || [],
        ...mutationBody(options)
      }
    })
    if (isMutationPlan(result) || 'message' in result) return result
    return {
      success: result.status === 'success',
      message: '提交成功',
      commitHash: 'commit' in result ? result.commit : undefined
    }
  }

  async push(options?: MutationOptions & { remote?: string; branch?: string | null }): Promise<GitOperationResult | MutationPlanDTO | GitPushResultDTO> {
    const result = await this.request<MutationPlanDTO | GitPushResultDTO>({
      method: 'POST',
      url: apiPath('/git/push'),
      data: {
        remote: options?.remote || 'origin',
        branch: options?.branch ?? null,
        ...mutationBody(options)
      }
    })
    return result
  }

  async deploy(message: string, _filePath?: string, options?: MutationOptions & { runBuildFirst?: boolean; push?: boolean }): Promise<GitOperationResult | MutationPlanDTO | TaskDTO> {
    const result = await this.request<MutationPlanDTO | TaskDTO>({
      method: 'POST',
      url: apiPath('/deploy'),
      data: {
        run_build_first: options?.runBuildFirst ?? true,
        commit_message: message,
        push: options?.push ?? true,
        ...mutationBody(options)
      },
      timeout: 120000
    })
    return result
  }

  async getSchema(): Promise<ContentSchemaDTO> {
    return this.request<ContentSchemaDTO>({
      method: 'GET',
      url: apiPath('/schema')
    })
  }

  async initSchema(options?: MutationOptions & { overwrite?: boolean }): Promise<MutationPlanDTO | SchemaInitResultDTO> {
    return this.request<MutationPlanDTO | SchemaInitResultDTO>({
      method: 'POST',
      url: apiPath('/schema/init'),
      data: {
        overwrite: options?.overwrite ?? false,
        ...mutationBody(options)
      }
    })
  }

  async rebuildSearchIndex(options?: { type?: ArticleType | null; force?: boolean }): Promise<SearchIndexResultDTO> {
    return this.request<SearchIndexResultDTO>({
      method: 'POST',
      url: apiPath('/search/index'),
      data: {
        type: options?.type ?? null,
        force: options?.force ?? false
      }
    })
  }

  async searchArticles(params: { q: string; type?: ArticleType; limit?: number; offset?: number }): Promise<SearchResultDTO> {
    return this.request<SearchResultDTO>({
      method: 'GET',
      url: apiPath('/search'),
      params: {
        q: params.q,
        type: params.type,
        limit: params.limit,
        offset: params.offset
      }
    })
  }

  async rebuildRegistryIndex(): Promise<RegistryIndexSyncResultDTO> {
    return this.request<RegistryIndexSyncResultDTO>({
      method: 'POST',
      url: apiPath('/registry-index/sync')
    })
  }

  async getRegistryIndexStats(): Promise<RegistryIndexStatsDTO> {
    return this.request<RegistryIndexStatsDTO>({
      method: 'GET',
      url: apiPath('/registry-index/stats')
    })
  }

  async getRegistryEntities(params?: RegistryIndexQueryParams): Promise<RegistryIndexListResponseDTO> {
    return this.request<RegistryIndexListResponseDTO>({
      method: 'GET',
      url: apiPath('/registry-index/entities'),
      params: {
        entity_type: params?.entityType || undefined,
        q: params?.q || undefined,
        status: params?.status || 'active',
        page: params?.page || 1,
        page_size: params?.pageSize || 20,
        sort: params?.sort || 'updated_at',
        order: params?.order || 'desc'
      }
    })
  }

  async getRegistryYaml(registryType: string): Promise<RegistryYamlFileDTO> {
    return this.request<RegistryYamlFileDTO>({
      method: 'GET',
      url: apiPath(`/registry-index/yaml/${encodeURIComponent(registryType)}`)
    })
  }

  async saveRegistryYaml(registryType: string, payload: RegistryYamlSaveDTO): Promise<RegistryIndexSyncResultDTO | RegistryYamlFileDTO> {
    return this.request<RegistryIndexSyncResultDTO | RegistryYamlFileDTO>({
      method: 'PUT',
      url: apiPath(`/registry-index/yaml/${encodeURIComponent(registryType)}`),
      data: payload
    })
  }

  async getRegistryYamlEntries(registryType: string): Promise<RegistryYamlEntriesDTO> {
    return this.request<RegistryYamlEntriesDTO>({
      method: 'GET',
      url: apiPath(`/registry-index/yaml/${encodeURIComponent(registryType)}/entries`)
    })
  }

  async saveRegistryYamlEntries(
    registryType: string,
    payload: RegistryYamlEntriesSaveDTO
  ): Promise<RegistryIndexSyncResultDTO | RegistryYamlEntriesDTO> {
    return this.request<RegistryIndexSyncResultDTO | RegistryYamlEntriesDTO>({
      method: 'PUT',
      url: apiPath(`/registry-index/yaml/${encodeURIComponent(registryType)}/entries`),
      data: payload
    })
  }

  async getRegistryDiff(registryType: string): Promise<RegistryDiffDTO> {
    return this.request<RegistryDiffDTO>({
      method: 'GET',
      url: apiPath(`/registry-index/diff/${encodeURIComponent(registryType)}`)
    })
  }

  async scanArticleIndex(): Promise<ArticleIndexScanResult> {
    const result = await this.rebuildSearchIndex({ force: true })
    return {
      scannedAt: new Date().toISOString(),
      articleCount: result.indexed_articles,
      draftCount: 0,
      indexStatus: result.status === 'success' ? 'rebuilt' : 'failed',
      failedFiles: []
    }
  }

  async getArticleIndex(): Promise<ArticleIndexSummary> {
    const posts = await this.getPosts()
    return {
      scannedAt: new Date().toISOString(),
      articleCount: posts.length,
      draftCount: posts.filter(post => post.status === 'draft').length,
      indexStatus: 'ready',
      failedFiles: [],
      articles: posts,
      categoryStats: posts.reduce<Record<string, number>>((stats, post) => {
        stats[post.category] = (stats[post.category] || 0) + 1
        return stats
      }, {}),
      tagStats: posts.reduce<Record<string, number>>((stats, post) => {
        for (const tag of post.tags || []) stats[tag] = (stats[tag] || 0) + 1
        return stats
      }, {}),
      statusStats: posts.reduce<Record<string, number>>((stats, post) => {
        stats[post.status] = (stats[post.status] || 0) + 1
        return stats
      }, {})
    }
  }

  async knowledgeQA(payload: KnowledgeQARequest): Promise<KnowledgeQAResponse> {
    if (payload.forceRescan) await this.rebuildSearchIndex({ force: true })
    const result = await this.searchArticles({
      q: payload.question,
      limit: 8,
      offset: 0
    })
    return {
      answer: result.results.length
        ? result.results.map(item => `- ${item.title}: ${item.snippet}`).join('\n')
        : '没有检索到匹配内容。',
      questionType: 'lookup',
      scannedAt: new Date().toISOString(),
      citations: result.results.map(item => ({
        title: item.title,
        path: item.article_id,
        snippet: item.snippet
      })),
      warnings: []
    }
  }

  async createAIDraft(payload: AIDraftRequestDTO): Promise<AIDraftResultDTO> {
    return this.request<AIDraftResultDTO>({
      method: 'POST',
      url: apiPath('/ai/draft'),
      data: payload
    })
  }

  async generateAgentPlan(payload: AgentPlanRequest): Promise<AgentPlanResponse> {
    const categoryRegistry = await this.getCategoryRegistry().catch(() => [])
    const primary = categoryRegistry[0]
    const title = payload.userInput.trim().split(/\r?\n/)[0]?.slice(0, 80) || '未命名草稿'
    const outline = payload.userInput
      .split(/\r?\n/)
      .map(line => line.trim())
      .filter(Boolean)
      .slice(1, 6)
    const draft = await this.createAIDraft({
      type: 'docs',
      title,
      outline,
      references: [],
      target_style: 'technical'
    })
    const plan: AIDraftPlan = {
      schemaVersion: 'admin-api-v1',
      approvalMode: payload.approvalMode,
      writingGoal: payload.writingGoal,
      userIntent: payload.userInput,
      inputType: 'text',
      clarificationRequired: false,
      clarificationQuestions: [],
      primarySlug: primary?.primarySlug || 'docs',
      primaryName: primary?.primaryName || '文档',
      prefix1: primary?.prefix1 || 'docs',
      prefix2: '',
      title: draft.title,
      tags: [],
      description: String(draft.frontmatter.description || ''),
      outline,
      imagePlaceholders: [],
      bodyMarkdown: draft.body,
      missingInfoQuestions: [],
      riskFlags: [],
      confidence: 0.8,
      reviewChecklist: [],
      rationale: '由后端 /api/v1/ai/draft 生成草稿。'
    }

    return {
      sessionId: payload.sessionId || draft.draft_id,
      plan,
      preview: {
        requiresManualApproval: payload.approvalMode === 'request-approval',
        approvalModeEffective: payload.approvalMode
      },
      validationErrors: [],
      warnings: []
    }
  }

  async commitAgentPlan(payload: AgentCommitRequest): Promise<AgentCommitResponse> {
    const detail = await this.createPost('', payload.plan.bodyMarkdown, {
      type: 'docs',
      title: payload.plan.title,
      slug: sanitizePathSegment(payload.plan.title),
      description: payload.plan.description || null,
      categoryPath: [payload.plan.primarySlug, payload.plan.prefix2].filter(Boolean),
      tags: payload.plan.tags
    })
    return {
      path: detail.path,
      created: true,
      written: true,
      editorUrl: `/editor?file=${encodeURIComponent(detail.path)}`,
      warnings: [],
      unusedImages: []
    }
  }

  async rewriteAIContent(payload: AIRewriteRequestDTO): Promise<AIRewriteResultDTO> {
    return this.request<AIRewriteResultDTO>({
      method: 'POST',
      url: apiPath('/ai/rewrite'),
      data: payload
    })
  }

  async fetchWebMaterial(payload: FetchWebRequestDTO): Promise<FetchWebResultDTO> {
    return this.request<FetchWebResultDTO>({
      method: 'POST',
      url: apiPath('/fetch/web'),
      data: payload
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

  setRetryConfig(config: Partial<RetryConfig>): void {
    this.retryConfig = { ...this.retryConfig, ...config }
  }
}

export const localAPI = new LocalAPIClient()

export type {
  LocalAPIError,
  RetryConfig
}

export { ErrorCode as LocalAPIErrorCode, createAPIError }
