/** 管理端 API 类型定义（从 admin/frontend 重构精简） */

export type ArticleType = 'docs' | 'blog'

export interface PostInfo {
  id: string
  type: ArticleType
  typeLabel: string
  filename: string
  path: string
  fullPath: string
  sha: string
  version: string
  route: string
  relativePath: string
  slug: string
  title: string
  category: string
  subCategory: string
  categories: string[]
  tags: string[]
  authors: string[]
  date: string | null
  lastUpdate?: { date?: string; author?: string } | null
  status: string
  description?: string
  lastModified: string
  categoryPath: string[]
  categoryLabel: string
  categoryKey: string
  displayStatus: string
  displayStatusLabel: string
  sidebarRegistered: boolean | null
  issues: ValidationIssue[]
}

export interface PostDetail extends PostInfo {
  content: string
  frontMatter: Record<string, unknown>
  body: string
  imageDir: string | null
  unusedImages: ImageInfo[]
}

export interface ImageInfo {
  path: string
  name: string
  size: number
  url: string
  markdownUrl: string
  markdown?: string
  referenced?: boolean
  lastModified?: string
  sha?: string
}

export interface ImageFolderInfo {
  folderPath: string
  articlePath: string
  articleExists: boolean
  imageCount: number
  images: ImageInfo[]
}

export interface CategoryDTO {
  type: ArticleType
  slug: string
  label: string
  path: string[]
  description?: string
  cover?: string
  sort_order?: number
  enabled?: boolean
  article_count?: number
  children?: CategoryDTO[]
}

export interface TagDTO {
  slug: string
  label: string
  description?: string | null
  usage_count: number
}

export interface TagCreateDTO {
  name: string
  slug?: string
}

export interface CategoryCreateDTO {
  type: ArticleType
  label: string
  slug: string
  parent_path?: string[]
  description?: string
  cover?: string
  sort_order?: number
}

export interface GitStatusDTO {
  branch: string
  clean: boolean
  ahead: number
  behind: number
  staged: string[]
  modified: string[]
  untracked: string[]
}

export interface GitOperationResult {
  success: boolean
  message: string
  commitHash?: string
}

export interface TaskDTO {
  task_id: string
  type: string
  status: string
  started_at?: string | null
  finished_at?: string | null
  exit_code?: number | null
  logs?: string
  error?: Record<string, unknown> | null
}

export interface PreviewStatusDTO {
  running: boolean
  port: number
  url: string
  pid?: number
}

export interface ValidationIssue {
  code: string
  message: string
  severity: string
}

export interface ContentSchemaDTO {
  version: string
  rules: Record<string, unknown>
}

export interface RegistryIndexStatsDTO {
  database_path: string
  entity_counts: Record<string, number>
  article_count: number
  category_count: number
  tag_count: number
  last_sync?: {
    id?: number
    status?: string
    finished_at?: string | null
  } | null
}

export interface RegistryIndexListResponseDTO {
  items: RegistryIndexItemDTO[]
  page: number
  page_size: number
  total: number
  has_next: boolean
}

export interface RegistryIndexItemDTO {
  id: number
  entity_type: string
  entity_key: string
  slug?: string | null
  title?: string | null
  display_name?: string | null
  status: string
  visibility: string
  source_kind: string
  source_path?: string | null
  updated_at?: string | null
  synced_at: string
  metadata: Record<string, unknown>
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

export interface SearchIndexResultDTO {
  status: string
  indexed_articles: number
  errors: string[]
}

export interface SearchResultDTO {
  query: string
  results: SearchHitDTO[]
  total: number
}

export interface SearchHitDTO {
  article_id: string
  title: string
  snippet: string
  type: string
  relative_path: string
}

export interface AIModelConfigDTO {
  id: string
  name: string
  provider?: string
  baseUrl: string
  modelId: string
  apiFormat?: 'openai' | 'anthropic'
  temperature?: number
  maxTokens?: number
  thinkingMode?: 'enabled' | 'disabled'
  reasoningEffort?: 'high' | 'max'
  isDefault?: boolean
  apiKey?: string
}

export interface AIModelTestResultDTO {
  success: boolean
  modelId?: string
}

export interface AIDraftRequestDTO {
  type: ArticleType
  title: string
  outline: string[]
  references: string[]
  target_style: string
}

export interface AIDraftResultDTO {
  draft_id: string
  title: string
  body: string
  frontmatter: Record<string, unknown>
}

export interface AIRewriteRequestDTO {
  content: string
  instruction: string
  model_id?: string
}

export interface AIRewriteResultDTO {
  content: string
  changes: string[]
}

export interface ArticleCreateOptions {
  type?: ArticleType
  title?: string
  slug?: string
  description?: string
  categoryPath?: string[]
  tags?: string[]
  authors?: string[]
  date?: string
  lastUpdate?: string
  sidebarPosition?: number
  prefix1?: string
  prefix2?: string
}

export interface ArticleDeleteOptions {
  withImages?: boolean
  dryRun?: boolean
  confirm?: boolean
}

export interface ArticleMoveOptions {
  targetType: ArticleType
  targetSlug: string
  targetCategoryPath?: string[]
  targetDate?: string
  replaceLinks?: boolean
  dryRun?: boolean
  confirm?: boolean
}

export interface ImageUploadOptions {
  slug?: string
  alt?: string
  mimeType?: string
}

export interface MutationOptions {
  dryRun?: boolean
  confirm?: boolean
}

export interface AssetCleanupResult {
  unusedImages: ImageInfo[]
  count: number
  missingReferences: string[]
  outOfScopeReferences: string[]
  deleted?: ImageInfo[]
}

export interface CategoryDeleteOptions {
  dryRun?: boolean
  confirm?: boolean
}

export interface CategoryRenameOptions {
  targetSlug: string
  targetLabel?: string
  replaceLinks?: boolean
  dryRun?: boolean
  confirm?: boolean
}

export interface DeployOptions {
  branch?: string
  runBuildFirst?: boolean
  cleanBuild?: boolean
  stageMode?: string
  paths?: string[]
  allowRebase?: boolean
  dryRun?: boolean
  confirm?: boolean
}

export interface GitPullOptions {
  branch?: string
  mode?: string
  runBuildAfter?: boolean
}

export interface RegistryIndexQueryParams {
  entityType?: string
  q?: string
  status?: string
  page?: number
  pageSize?: number
  sort?: string
  order?: string
}

export interface DeployResultDTO {
  status: string
  message: string
  task_id?: string
}

export interface GitCommitResultDTO {
  status: string
  commit: string
}

export interface GitPushResultDTO {
  status: string
  message: string
}

export interface GitCommandResultDTO {
  status: 'success' | 'failed'
  branch?: string | null
  logs: string
  error?: Record<string, string> | null
}

export interface GitSyncStatusDTO {
  current_branch: string
  remote_url?: string | null
  git_user_name?: string | null
  git_user_email?: string | null
  ssh_key_path: string
  public_key?: string | null
  has_private_key: boolean
  remote_uses_ssh: boolean
  is_dirty: boolean
  changes: string[]
}

export interface DocusaurusConfigNavItemDTO {
  to: string
  label?: string | null
  dropdown_label?: string | null
  exists?: boolean | null
}

export interface DocusaurusConfigStatusDTO {
  config_exists: boolean
  config_path: string
  nav_item_total: number
  nav_items: DocusaurusConfigNavItemDTO[]
  broken_to_links: DocusaurusConfigNavItemDTO[]
  docs_top_category_total: number
  docs_top_categories_missing_in_nav: Array<{ slug: string; label: string }>
  blog_top_category_total: number
  blog_top_categories_missing_in_nav: Array<{ slug: string; label: string }>
  stale_blog_nav_items: DocusaurusConfigNavItemDTO[]
}

export interface SiteValidationResultDTO {
  valid: boolean
  errors: ValidationIssue[]
  warnings: ValidationIssue[]
}

export interface SidebarStatusDTO {
  type: string
  sidebars_exists: boolean
  sidebars_path?: string | null
  docs_count: number
  registered_count: number
  missing_count: number
  orphan_count: number
  registered_doc_ids: string[]
  missing_in_sidebars: string[]
  orphan_sidebar_ids: string[]
}

export interface RegistryDiffDTO {
  added: string[]
  removed: string[]
  modified: string[]
}

export interface RegistryYamlFileDTO {
  type: string
  content: string
  entries: unknown[]
}

export interface RegistryYamlEntriesDTO {
  type: string
  entries: unknown[]
}

export interface RegistryYamlSaveDTO {
  content: string
}

export interface RegistryYamlEntriesSaveDTO {
  entries: unknown[]
}

export interface SchemaInitResultDTO {
  status: string
  message: string
}

export interface DirectoryItem {
  name: string
  path: string
  is_dir: boolean
  children?: DirectoryItem[]
}

export interface FetchWebRequestDTO {
  url: string
  selector?: string
}

export interface FetchWebResultDTO {
  url: string
  title: string
  content: string
  html: string
}

export interface BlogAPI {
  loginAdmin(username: string, password: string): Promise<unknown>
  getPosts(): Promise<PostInfo[]>
  getPost(articleId: string): Promise<PostDetail>
  createPost(path: string, content: string, options?: ArticleCreateOptions): Promise<PostDetail>
  updatePost(articleId: string, content: string, expectedVersion?: string): Promise<PostDetail>
  deletePost(articleId: string, sha?: string, options?: ArticleDeleteOptions): Promise<unknown>
  movePost(articleId: string, options: ArticleMoveOptions): Promise<unknown>
  getCategories(params?: { type?: ArticleType; includeEmpty?: boolean; includeCounts?: boolean }): Promise<CategoryDTO[]>
  createCategory(payload: CategoryCreateDTO): Promise<CategoryDTO>
  getTags(params?: { keyword?: string; page?: number; pageSize?: number; sort?: string }): Promise<TagDTO[]>
  createTag(payload: TagCreateDTO): Promise<TagDTO>
  checkHealth(): Promise<boolean>
  getGitStatus(includeUntracked?: boolean): Promise<GitStatusDTO>
  runBuild(clean?: boolean): Promise<TaskDTO>
  startPreview(options?: { port?: number; host?: string; openBrowser?: boolean }): Promise<PreviewStatusDTO>
  getAIModels(): Promise<AIModelConfigDTO[]>
  saveAIModel(model: AIModelConfigDTO & { apiKey?: string }): Promise<AIModelConfigDTO>
  rebuildRegistryIndex(): Promise<RegistryIndexSyncResultDTO>
  getRegistryIndexStats(): Promise<RegistryIndexStatsDTO>
  validateArticle(articleId: string): Promise<{ article_id: string; issues: ValidationIssue[] }>
  validateSite(options?: { includeImages?: boolean; includeLinks?: boolean; includeSidebars?: boolean; type?: ArticleType | null }): Promise<SiteValidationResultDTO>
  commit(message: string, options?: MutationOptions & { paths?: string[] }): Promise<GitOperationResult | unknown>
  push(options?: MutationOptions & { remote?: string; branch?: string | null }): Promise<GitOperationResult | unknown>
  deploy(message: string, filePath?: string, options?: DeployOptions): Promise<unknown>
  uploadImage(articleId: string, imageData: Uint8Array | ArrayBuffer, filename: string, options?: ImageUploadOptions): Promise<ImageInfo>
  getImages(articleId: string): Promise<ImageInfo[]>
  deleteImage(path: string, sha?: string, options?: MutationOptions): Promise<unknown>
  scanUnusedImages(articleId: string): Promise<AssetCleanupResult>
  cleanupUnusedImages(articleId: string): Promise<AssetCleanupResult>
  getImageFolders(): Promise<ImageFolderInfo[]>
  searchArticles(params: { q: string; type?: ArticleType; limit?: number; offset?: number }): Promise<SearchResultDTO>
  rebuildSearchIndex(options?: { type?: ArticleType | null; force?: boolean }): Promise<SearchIndexResultDTO>
  getSidebarStatus(includeDetails?: boolean): Promise<SidebarStatusDTO>
  syncSidebars(options?: MutationOptions & { mode?: string }): Promise<unknown>
  syncBackendIndex(options?: MutationOptions): Promise<unknown>
  syncSiteConfig(options?: MutationOptions): Promise<unknown>
  getDocusaurusConfigStatus(): Promise<DocusaurusConfigStatusDTO>
  syncDocusaurusConfig(options?: MutationOptions & { mode?: string }): Promise<unknown>
  getSchema(): Promise<ContentSchemaDTO>
  initSchema(options?: MutationOptions & { overwrite?: boolean }): Promise<unknown>
  syncTags(options?: MutationOptions): Promise<unknown>
  renameCategory(categoryId: string, options: CategoryRenameOptions): Promise<unknown>
  deleteCategory(categoryId: string, options?: CategoryDeleteOptions): Promise<unknown>
  getRegistryYaml(registryType: string): Promise<RegistryYamlFileDTO>
  saveRegistryYaml(registryType: string, payload: RegistryYamlSaveDTO): Promise<unknown>
  getRegistryYamlEntries(registryType: string): Promise<RegistryYamlEntriesDTO>
  saveRegistryYamlEntries(registryType: string, payload: RegistryYamlEntriesSaveDTO): Promise<unknown>
  getRegistryDiff(registryType: string): Promise<RegistryDiffDTO>
  getRegistryEntities(params?: RegistryIndexQueryParams): Promise<RegistryIndexListResponseDTO>
  createAIDraft(payload: AIDraftRequestDTO): Promise<AIDraftResultDTO>
  rewriteAIContent(payload: AIRewriteRequestDTO): Promise<AIRewriteResultDTO>
  deleteAIModel(modelId: string): Promise<AIModelConfigDTO[]>
  testAIModel(modelId: string): Promise<AIModelTestResultDTO>
  getGitSyncStatus(): Promise<GitSyncStatusDTO>
  createGitSshKey(options?: { email?: string; overwrite?: boolean }): Promise<GitCommandResultDTO>
  updateGitRemote(remoteUrl: string): Promise<GitCommandResultDTO>
  testGitSsh(): Promise<GitCommandResultDTO>
  pullFromGitHub(options?: GitPullOptions): Promise<GitCommandResultDTO>
  fetchWebMaterial(payload: FetchWebRequestDTO): Promise<FetchWebResultDTO>
  getBuildTask(taskId: string): Promise<TaskDTO>
  getPreviewStatus(): Promise<PreviewStatusDTO>
}
