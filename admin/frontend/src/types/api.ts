/**
 * 统一 API 类型定义
 * 用于统一本地 API 的调用
 */
import type {
  AIChatRequest,
  AIChatResponse,
  AgentRunResponse,
  AgentCommitRequest,
  AgentCommitResponse,
  AgentPlanRequest,
  AgentPlanResponse,
  ApprovalResumeRequest,
  ArticleIndexScanResult,
  ArticleIndexSummary,
  CategoryRegistryItem,
  EditorAgentRunRequest,
  KnowledgeAgentRunRequest,
  KnowledgeQARequest,
  KnowledgeQAResponse,
  WritingAgentRunRequest,
  WritingMaterialExtractResponse
} from '@/types/ai-writing'

/**
 * Front Matter 结构
 */
export interface FrontMatter {
  title: string
  date?: string
  updated?: string
  categories?: string[]
  tags?: string[]
  authors?: string[]
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
  /** 后端文章 ID */
  id?: string
  /** 内容类型 */
  type?: 'docs' | 'blog'
  /** 内容类型显示名 */
  typeLabel?: string
  /** 文件名（不含扩展名） */
  filename: string
  /** 文章 ID（兼容旧字段名 path） */
  path: string
  /** 后端返回的相对文章路径 */
  fullPath?: string
  /** SHA 值（兼容旧接口字段） */
  sha?: string
  /** 乐观锁版本 */
  version?: string
  /** Docusaurus 路由 */
  route?: string
  /** 相对 docs/blog 根目录路径 */
  relativePath?: string
  /** slug/doc id */
  slug?: string
  /** 作者列表 */
  authors?: string[]
  /** docs 分类路径 */
  categoryPath?: string[]
  /** 后端解析出的当前分类显示名 */
  categoryLabel?: string
  /** 前端分组使用的稳定分类 key */
  categoryKey?: string
  /** 校验状态 */
  displayStatus?: 'ok' | 'warning' | 'error'
  /** 校验状态显示名 */
  displayStatusLabel?: string
  /** docs 是否登记到 sidebars.ts */
  sidebarRegistered?: boolean | null
  /** 校验问题 */
  issues?: ValidationIssue[]
  /** 文章标题 */
  title: string
  /** 一级分类 */
  category: string
  /** 二级分类 */
  subCategory?: string
  /** 分类路径或旧博客分类数组 */
  categories?: string[]
  /** 标签列表 */
  tags: string[]
  /** 创建日期 */
  date: string
  /** 更新日期 */
  updated?: string
  /** 旧字段兼容；列表展示请使用 displayStatus/displayStatusLabel */
  status: string
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
  /** 文章图片目录 */
  imageDir?: string | null
  /** 保存后检测到的未引用图片 */
  unusedImages?: ImageInfo[]
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
  /** Markdown 中使用的相对 URL */
  markdownUrl?: string
  /** 完整 Markdown 图片语法 */
  markdown?: string
  /** 是否被文章正文引用 */
  referenced?: boolean
  /** SHA 值（兼容旧接口字段） */
  sha?: string
  /** 最后修改时间 */
  lastModified?: string
}

/**
 * 图片资源文件夹
 */
export interface ImageFolderInfo {
  /** 相对于 _posts 的资源文件夹路径，不含 .md */
  folderPath: string
  /** 对应文章路径；存在文章时带 .md，孤立文件夹时等于 folderPath */
  articlePath: string
  /** 是否存在对应 Markdown 文章 */
  articleExists: boolean
  /** 图片数量 */
  imageCount: number
  /** 文件夹下的图片 */
  images: ImageInfo[]
}

/**
 * 图片资源清理结果
 */
export interface AssetCleanupResult {
  unusedImages?: ImageInfo[]
  deleted?: ImageInfo[]
  count?: number
  missingReferences?: string[]
  outOfScopeReferences?: string[]
}

export interface ValidationIssue {
  code: string
  message: string
  severity: 'error' | 'warning' | string
}

export interface ArticleCreateOptions {
  type?: 'docs' | 'blog'
  title?: string
  slug?: string
  description?: string | null
  categoryPath?: string[]
  sidebarPosition?: number | null
  authors?: string[]
  tags?: string[]
  date?: string | null
}

export interface FileChangeDTO {
  action: 'create' | 'update' | 'delete' | 'move' | 'replace' | string
  target: string
  from?: string | null
  to?: string | null
  description: string
}

export interface MutationPlanDTO {
  dry_run: boolean
  requires_confirmation: boolean
  changes: FileChangeDTO[]
  warnings: string[]
}

export interface MutationOptions {
  dryRun?: boolean
  confirm?: boolean
}

export interface TaskDTO {
  task_id: string
  type: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled' | string
  started_at?: string | null
  finished_at?: string | null
  exit_code?: number | null
  logs?: string
  error?: Record<string, unknown> | null
}

export interface ArticleValidationResultDTO {
  article_id: string
  issues: ValidationIssue[]
}

export interface ArticleMoveOptions extends MutationOptions {
  targetType: 'docs' | 'blog'
  targetSlug: string
  targetCategoryPath?: string[]
  targetDate?: string | null
  replaceLinks?: boolean
}

export interface ArticleDeleteOptions extends MutationOptions {
  withImages?: boolean
}

export interface ImageUploadOptions {
  slug?: string
  alt?: string
  mimeType?: string
}

export interface CategoryDTO {
  type: 'docs' | 'blog' | string
  slug: string
  label: string
  path: string[]
  description?: string | null
  cover?: string | null
  sort_order?: number | null
  enabled?: boolean
  article_count?: number | null
  children: CategoryDTO[]
}

export interface CategoryCreateDTO {
  type: 'docs' | 'blog' | string
  slug: string
  label: string
  parent_path?: string[]
  description?: string | null
  cover?: string | null
}

export interface TagDTO {
  slug: string
  label: string
  description?: string | null
  usage_count: number
}

export interface TagCreateDTO {
  label: string
  slug?: string | null
  description?: string | null
}

export interface TagSyncResultDTO {
  dry_run: boolean
  requires_confirmation: boolean
  discovered_count: number
  existing_count: number
  created_tags: TagDTO[]
  warnings: string[]
}

export interface SidebarStatusDTO {
  registered_doc_ids: string[]
  missing_in_sidebars: string[]
  orphan_sidebar_ids: string[]
}

export interface SiteValidationResultDTO {
  summary: {
    article_count: number
    error_count: number
    warning_count: number
  }
  issues: Array<ValidationIssue & {
    scope?: string
    article_id?: string | null
  }>
}

export interface PreviewStatusDTO {
  status: 'running' | 'stopped' | 'failed' | string
  url: string | null
  pid: number | null
}

export interface GitStatusDTO {
  branch: string
  is_dirty: boolean
  files: Array<{
    path: string
    status: string
  }>
}

export interface GitCommitResultDTO {
  commit: string
  message: string
}

export interface GitPushResultDTO {
  status: string
  remote: string
  branch: string
}

export interface ContentSchemaDTO {
  categories: CategoryDTO[]
  tags: TagDTO[]
  frontmatter: Record<string, unknown>
}

export interface SchemaInitResultDTO {
  created: string[]
  skipped: string[]
}

export interface SearchIndexResultDTO {
  indexed_articles: number
  status: string
}

export interface SearchResultDTO {
  query: string
  total: number
  limit: number
  offset: number
  results: Array<{
    article_id: string
    title: string
    route: string
    snippet: string
  }>
}

export interface RegistryIndexItemDTO {
  id: number
  entity_type: 'category' | 'tag' | 'article' | string
  entity_key: string
  slug?: string | null
  title?: string | null
  display_name?: string | null
  description?: string | null
  summary?: string | null
  status: string
  visibility: string
  sort_order: number
  priority: number
  source_kind: 'yaml' | 'markdown' | 'generated' | 'manual' | string
  source_path?: string | null
  created_at?: string | null
  updated_at?: string | null
  synced_at: string
  metadata: Record<string, unknown>
}

export interface RegistryIndexListResponseDTO {
  items: RegistryIndexItemDTO[]
  page: number
  page_size: number
  total: number
  has_next: boolean
}

export interface RegistryIndexSyncResultDTO {
  sync_id: number
  sync_type: string
  status: string
  database_path: string
  scanned_files: number
  changed_files: number
  upserted_entities: number
  deleted_entities: number
  error_count: number
  message?: string | null
}

export interface RegistryIndexStatsDTO {
  database_path: string
  entity_counts: Record<string, number>
  article_count: number
  category_count: number
  tag_count: number
  last_sync?: Record<string, unknown> | null
}

export interface RegistryYamlFileDTO {
  registry_type: string
  path: string
  exists: boolean
  content: string
}

export interface RegistryYamlSaveDTO {
  content: string
  rebuild_index?: boolean
}

export interface RegistryYamlEntriesDTO {
  registry_type: string
  path: string
  exists: boolean
  items: Record<string, unknown>[]
}

export interface RegistryYamlEntriesSaveDTO {
  items: Record<string, unknown>[]
  rebuild_index?: boolean
}

export interface RegistryDiffDTO {
  registry_type: string
  sqlite_entity_type: string
  yaml_count: number
  sqlite_count: number
  missing_in_sqlite: string[]
  missing_in_yaml: string[]
  checked_at: string
}

export interface RegistryIndexQueryParams {
  entityType?: 'category' | 'tag' | 'article' | string | null
  q?: string | null
  status?: string
  page?: number
  pageSize?: number
  sort?: string
  order?: 'asc' | 'desc'
}

export interface AIDraftRequestDTO {
  type: 'docs' | 'blog'
  title: string
  outline?: string[]
  references?: string[]
  target_style?: string
}

export interface AIDraftResultDTO {
  draft_id: string
  title: string
  frontmatter: Record<string, unknown>
  body: string
}

export interface AIRewriteRequestDTO {
  article_id?: string | null
  instruction: string
  selection: string
  apply_directly?: boolean
  expected_version?: string | null
}

export interface AIRewriteResultDTO {
  original: string
  rewritten: string
  requires_approval: boolean
  applied: boolean
  article_id: string | null
}

export interface FetchWebRequestDTO {
  url: string
  extract?: Array<'title' | 'summary' | 'images' | 'links' | 'markdown' | string>
  download_images?: boolean
}

export interface FetchWebResultDTO {
  url: string
  title: string | null
  summary: string | null
  images: Record<string, unknown>[]
  links: Record<string, unknown>[]
  markdown: string | null
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
 * 定义本地 API 的统一接口
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
   * @param options 可选参数（prefix1/prefix2 兼容旧创建流程）
   */
  createPost(path: string, content: string, options?: ArticleCreateOptions & { prefix1?: string; prefix2?: string }): Promise<PostInfo | PostDetail | GitOperationResult>

  /**
   * 更新文章
   * @param path 文章路径
   * @param content 文章内容
   * @param sha 文件 SHA 值（兼容旧接口字段）
   */
  updatePost(path: string, content: string, sha?: string): Promise<PostInfo | PostDetail | GitOperationResult>

  /**
   * 删除文章
   * @param path 文章路径
   * @param sha 文件 SHA 值（兼容旧接口字段）
   */
  deletePost(path: string, sha?: string, options?: ArticleDeleteOptions): Promise<void | MutationPlanDTO | GitOperationResult>

  /**
   * 按文档接口移动或重命名文章
   */
  movePost?(articleId: string, options: ArticleMoveOptions): Promise<MutationPlanDTO>

  /**
   * 按文档接口校验单篇文章
   */
  validateArticle?(articleId: string): Promise<ArticleValidationResultDTO>

  /**
   * 获取分类目录列表
   */
  getCategories?(params?: { type?: 'docs' | 'blog'; includeEmpty?: boolean; includeCounts?: boolean }): Promise<CategoryDTO[] | DirectoryItem[]>

  createCategory?(payload: CategoryCreateDTO): Promise<CategoryDTO>

  /**
   * 获取文章创建分类注册表
   */
  getCategoryRegistry?(): Promise<CategoryRegistryItem[]>

  /**
   * 保存文章创建分类注册表
   */
  updateCategoryRegistry?(registry: CategoryRegistryItem[]): Promise<CategoryRegistryItem[]>

  /**
   * 获取指定分类下的文章列表
   * @param category 分类名称
   */
  getPostsByCategory?(category: string): Promise<PostInfo[]>

  // ==================== 图片管理 ====================

  /**
   * 上传图片
   * @param path 文章路径
   * @param content 图片数据
   * @param filename 图片文件名
   */
  uploadImage(path: string, content: Uint8Array | ArrayBuffer, filename?: string, options?: ImageUploadOptions): Promise<ImageInfo | GitOperationResult>

  /**
   * 删除图片
   * @param path 图片路径
   * @param sha 文件 SHA 值（兼容旧接口字段）
   */
  deleteImage(path: string, sha?: string, options?: MutationOptions): Promise<void | MutationPlanDTO | GitOperationResult>

  /**
   * 获取图片列表
   * @param articlePath 文章路径
   */
  getImages?(articlePath: string): Promise<ImageInfo[]>

  /**
   * 获取所有含图片的资源文件夹
   */
  getImageFolders?(): Promise<ImageFolderInfo[]>

  /**
   * 扫描当前文章未引用图片
   */
  scanUnusedImages?(articlePath: string, content: string): Promise<AssetCleanupResult>

  /**
   * 移动当前文章未引用图片到 _unused
   */
  cleanupUnusedImages?(articlePath: string, content: string): Promise<AssetCleanupResult>

  getTags?(params?: { keyword?: string; page?: number; pageSize?: number; sort?: string }): Promise<TagDTO[]>

  createTag?(payload: TagCreateDTO): Promise<TagDTO>

  syncTags?(options?: MutationOptions): Promise<TagSyncResultDTO>

  getSidebarStatus?(includeDetails?: boolean): Promise<SidebarStatusDTO>

  syncSidebars?(options?: MutationOptions & { mode?: 'append_missing' | 'regenerate' | string }): Promise<MutationPlanDTO>

  validateSite?(options?: { includeImages?: boolean; includeLinks?: boolean; includeSidebars?: boolean; type?: 'docs' | 'blog' | null }): Promise<SiteValidationResultDTO>

  // ==================== Git 操作 ====================

  runBuild?(clean?: boolean): Promise<TaskDTO>

  getBuildTask?(taskId: string): Promise<TaskDTO>

  startPreview?(options?: { port?: number; host?: string; openBrowser?: boolean }): Promise<PreviewStatusDTO>

  getPreviewStatus?(): Promise<PreviewStatusDTO>

  getGitStatus?(includeUntracked?: boolean): Promise<GitStatusDTO>

  /**
   * 提交更改
   * @param message 提交信息
   */
  commit?(message: string, options?: MutationOptions & { paths?: string[] }): Promise<GitOperationResult | MutationPlanDTO | GitCommitResultDTO>

  /**
   * 推送到远程
   */
  push?(options?: MutationOptions & { remote?: string; branch?: string | null }): Promise<GitOperationResult | MutationPlanDTO | GitPushResultDTO>

  /**
   * 部署（commit + push）
   * @param message 提交信息
   * @param filePath 指定提交的文件路径（相对于仓库根目录），为空则提交所有变更
   */
  deploy(message: string, filePath?: string, options?: MutationOptions & { runBuildFirst?: boolean; push?: boolean }): Promise<GitOperationResult | MutationPlanDTO | TaskDTO>

  getSchema?(): Promise<ContentSchemaDTO>

  initSchema?(options?: MutationOptions & { overwrite?: boolean }): Promise<MutationPlanDTO | SchemaInitResultDTO>

  rebuildSearchIndex?(options?: { type?: 'docs' | 'blog' | null; force?: boolean }): Promise<SearchIndexResultDTO>

  searchArticles?(params: { q: string; type?: 'docs' | 'blog'; limit?: number; offset?: number }): Promise<SearchResultDTO>

  rebuildRegistryIndex?(): Promise<RegistryIndexSyncResultDTO>

  getRegistryIndexStats?(): Promise<RegistryIndexStatsDTO>

  getRegistryEntities?(params?: RegistryIndexQueryParams): Promise<RegistryIndexListResponseDTO>

  getRegistryYaml?(registryType: string): Promise<RegistryYamlFileDTO>

  saveRegistryYaml?(registryType: string, payload: RegistryYamlSaveDTO): Promise<RegistryIndexSyncResultDTO | RegistryYamlFileDTO>

  getRegistryYamlEntries?(registryType: string): Promise<RegistryYamlEntriesDTO>

  saveRegistryYamlEntries?(registryType: string, payload: RegistryYamlEntriesSaveDTO): Promise<RegistryIndexSyncResultDTO | RegistryYamlEntriesDTO>

  getRegistryDiff?(registryType: string): Promise<RegistryDiffDTO>

  // ==================== AI 写作 ====================

  createAIDraft?(payload: AIDraftRequestDTO): Promise<AIDraftResultDTO>

  rewriteAIContent?(payload: AIRewriteRequestDTO): Promise<AIRewriteResultDTO>

  fetchWebMaterial?(payload: FetchWebRequestDTO): Promise<FetchWebResultDTO>

  /**
   * AI 对话，返回 Agent 草稿方案或 LLM 编辑操作
   */
  aiChat?(payload: AIChatRequest): Promise<AIChatResponse>

  /**
   * 生成 Agent 草稿方案
   */
  generateAgentPlan?(payload: AgentPlanRequest): Promise<AgentPlanResponse>

  /**
   * 提交已确认的 Agent 草稿方案并创建文章
   */
  commitAgentPlan?(payload: AgentCommitRequest): Promise<AgentCommitResponse>

  /**
   * 提取上传素材中的文本内容
   */
  extractWritingMaterial?(file: File): Promise<WritingMaterialExtractResponse>

  /**
   * 扫描并重建本地文章索引
   */
  scanArticleIndex?(): Promise<ArticleIndexScanResult>

  /**
   * 获取本地文章索引摘要
   */
  getArticleIndex?(): Promise<ArticleIndexSummary>

  /**
   * 基于本地知识库问答
   */
  knowledgeQA?(payload: KnowledgeQARequest): Promise<KnowledgeQAResponse>

  runEditorAgent?(payload: EditorAgentRunRequest): Promise<AgentRunResponse>

  runWritingAgent?(payload: WritingAgentRunRequest): Promise<AgentRunResponse>

  runKnowledgeAgent?(payload: KnowledgeAgentRunRequest): Promise<AgentRunResponse<KnowledgeQAResponse>>

  resumeAgentApproval?(approvalId: string, payload: ApprovalResumeRequest): Promise<AgentRunResponse | unknown>

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
