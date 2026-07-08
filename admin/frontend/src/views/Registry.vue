<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from 'vue'
import {
  NAlert,
  NButton,
  NCard,
  NDataTable,
  NDynamicTags,
  NEmpty,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NModal,
  NPopconfirm,
  NSelect,
  NSpace,
  NStatistic,
  NSwitch,
  NTabPane,
  NTabs,
  NTag,
  useMessage,
  type DataTableColumns,
  type PaginationProps,
  type SelectOption
} from 'naive-ui'
import { getAPI } from '@/api/index'
import type {
  CategoryDTO,
  DocusaurusConfigStatusDTO,
  FileChangeDTO,
  MutationPlanDTO,
  RegistryIndexItemDTO,
  RegistryIndexListResponseDTO,
  RegistryIndexStatsDTO,
  RegistryIndexSyncResultDTO,
  RegistryDiffDTO,
  RegistryYamlEntriesDTO,
  RegistryYamlFileDTO,
  SidebarStatusDTO
} from '@/types/api'

type EntityType = 'category' | 'tag' | 'article' | null
type RegistryType = 'categories' | 'tags'

const api = getAPI()
const message = useMessage()

const stats = ref<RegistryIndexStatsDTO | null>(null)
const lastSync = ref<RegistryIndexSyncResultDTO | null>(null)
const activePanel = ref('index')
const isStatsLoading = ref(false)
const isTableLoading = ref(false)
const isSyncing = ref(false)
const isTagSyncing = ref(false)
const isYamlLoading = ref(false)
const isYamlSaving = ref(false)
const isDiffLoading = ref(false)
const isCategoryLoading = ref(false)
const isCategoryPlanLoading = ref(false)
const isCategoryDeleting = ref(false)
const isCategoryRenamePlanLoading = ref(false)
const isCategoryRenaming = ref(false)
const yamlRegistryType = ref<RegistryType>('categories')
const yamlFile = ref<RegistryYamlFileDTO | null>(null)
const yamlContent = ref('')
const yamlEntries = ref<RegistryYamlEntriesDTO | null>(null)
const selectedEntryIndex = ref(0)
const diffResult = ref<RegistryDiffDTO | null>(null)
const categoryTree = ref<CategoryDTO[]>([])
const categorySearchValue = ref('')
const showEmptyCategories = ref(true)
const selectedCategoryId = ref<string | null>(null)
const expandedCategoryIds = ref<Set<string>>(new Set())
const deleteCategoryTarget = ref<CategoryDTO | null>(null)
const deleteCategoryPlan = ref<MutationPlanDTO | null>(null)
const renameCategoryTarget = ref<CategoryDTO | null>(null)
const renameCategoryPlan = ref<MutationPlanDTO | null>(null)
const sidebarStatus = ref<SidebarStatusDTO | null>(null)
const isSidebarLoading = ref(false)
const isSidebarSyncing = ref(false)
const docusaurusStatus = ref<DocusaurusConfigStatusDTO | null>(null)
const isDocusaurusLoading = ref(false)
const isDocusaurusSyncing = ref(false)

type CategoryListItem = {
  category: CategoryDTO
  depth: number
  childCount: number
}

const entryForm = reactive({
  type: 'docs',
  slug: '',
  pathText: '',
  label: '',
  aliases: [] as string[],
  description: '',
  cover: '',
  sort_order: null as number | null,
  enabled: true,
  id: '',
  body_path: ''
})

const renameCategoryForm = reactive({
  targetSlug: '',
  targetLabel: '',
  replaceLinks: true
})

const filters = reactive({
  entityType: 'category' as EntityType,
  keyword: '',
  status: 'active',
  sort: 'updated_at',
  order: 'desc' as 'asc' | 'desc',
  page: 1,
  pageSize: 20
})

const entities = ref<RegistryIndexListResponseDTO>({
  items: [],
  page: 1,
  page_size: 20,
  total: 0,
  has_next: false
})

const entityTypeOptions: SelectOption[] = [
  { label: '全部实体', value: '__all' },
  { label: '分类', value: 'category' },
  { label: '标签', value: 'tag' },
  { label: '文章索引', value: 'article' }
]

const sortOptions: SelectOption[] = [
  { label: '最近更新', value: 'updated_at' },
  { label: '同步时间', value: 'synced_at' },
  { label: '显示名称', value: 'display_name' },
  { label: '实体键', value: 'entity_key' },
  { label: '排序值', value: 'sort_order' }
]

const orderOptions: SelectOption[] = [
  { label: '降序', value: 'desc' },
  { label: '升序', value: 'asc' }
]

const statusOptions: SelectOption[] = [
  { label: '有效', value: 'active' },
  { label: '隐藏', value: 'hidden' },
  { label: '全部状态', value: 'all' }
]

const registryOptions: SelectOption[] = [
  { label: '分类 categories.yml', value: 'categories' },
  { label: '标签 tags.yml', value: 'tags' }
]

const summaryCards = computed(() => [
  { label: '分类', value: stats.value?.category_count ?? 0, tone: 'green' },
  { label: '标签', value: stats.value?.tag_count ?? 0, tone: 'blue' },
  { label: '文章索引', value: stats.value?.article_count ?? 0, tone: 'olive' }
])

const lastSyncText = computed(() => {
  const sync = stats.value?.last_sync
  const finishedAt = sync?.finished_at
  if (!finishedAt) return '尚未同步'
  return formatDateTime(String(finishedAt))
})

const databasePath = computed(() => stats.value?.database_path || '未生成')

const pagination = computed<PaginationProps>(() => ({
  page: filters.page,
  pageSize: filters.pageSize,
  itemCount: entities.value.total,
  pageSizes: [10, 20, 50, 100],
  showSizePicker: true,
  prefix: ({ itemCount }) => `共 ${itemCount} 条`
}))

const columns: DataTableColumns<RegistryIndexItemDTO> = [
  {
    title: '实体',
    key: 'title',
    minWidth: 260,
    ellipsis: {
      tooltip: true
    },
    render(row) {
      return h('div', { class: 'entity-cell' }, [
        h('div', { class: 'entity-title' }, row.display_name || row.title || row.entity_key),
        h('div', { class: 'entity-key mono' }, row.entity_key)
      ])
    }
  },
  {
    title: '类型',
    key: 'entity_type',
    width: 110,
    render(row) {
      return h(
        NTag,
        { size: 'small', type: tagType(row.entity_type), round: true },
        { default: () => entityTypeLabel(row.entity_type) }
      )
    }
  },
  {
    title: '来源',
    key: 'source_kind',
    width: 110,
    render(row) {
      return h(NTag, { size: 'small', bordered: false, round: true }, { default: () => sourceKindLabel(row.source_kind) })
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row) {
      return h(
        NTag,
        { size: 'small', type: row.status === 'active' ? 'success' : 'warning', round: true },
        { default: () => row.status }
      )
    }
  },
  {
    title: '来源路径',
    key: 'source_path',
    minWidth: 240,
    ellipsis: {
      tooltip: true
    },
    render(row) {
      return h('span', { class: 'mono path-text' }, row.source_path || '-')
    }
  },
  {
    title: '同步时间',
    key: 'synced_at',
    width: 180,
    render(row) {
      return formatDateTime(row.synced_at)
    }
  }
]

const yamlEntryColumns = computed<DataTableColumns<Record<string, unknown>>>(() => [
  {
    title: '键',
    key: 'key',
    minWidth: 200,
    ellipsis: {
      tooltip: true
    },
    render(row, index) {
      return h(
        NButton,
        {
          text: true,
          type: selectedEntryIndex.value === index ? 'primary' : 'default',
          onClick: () => selectEntry(index)
        },
        { default: () => yamlEntryKey(row) || `条目 ${index + 1}` }
      )
    }
  },
  {
    title: '显示名',
    key: 'label',
    minWidth: 160,
    ellipsis: {
      tooltip: true
    },
    render(row) {
      return String(row.label || row.name || row.title || '-')
    }
  }
])

const allCategoryItems = computed(() => flattenCategoryItems(categoryTree.value))

const categorySummary = computed(() => {
  const items = allCategoryItems.value
  return {
    total: items.length,
    empty: items.filter((item) => (item.category.article_count ?? 0) === 0).length,
    articleCount: items.reduce((count, item) => count + (item.category.article_count ?? 0), 0)
  }
})

const visibleCategoryItems = computed(() => {
  const keyword = categorySearchValue.value.trim().toLowerCase()
  const visible: CategoryListItem[] = []

  const walk = (categories: CategoryDTO[], depth: number, parentVisible: boolean) => {
    for (const category of categories) {
      const childCount = category.children?.length || 0
      const isEmpty = (category.article_count ?? 0) === 0
      const matches = !keyword || categoryMatches(category, keyword) || hasMatchingDescendant(category, keyword)
      const passesEmpty = showEmptyCategories.value || !isEmpty
      const shouldShow = parentVisible && matches && passesEmpty

      if (shouldShow) {
        visible.push({ category, depth, childCount })
      }

      const expanded = keyword ? matches : expandedCategoryIds.value.has(category.id)
      if (expanded && childCount > 0) {
        walk(category.children, depth + 1, shouldShow || Boolean(keyword))
      }
    }
  }

  walk(categoryTree.value, 0, true)
  return visible
})

const selectedCategory = computed(() => {
  if (selectedCategoryId.value) {
    return allCategoryItems.value.find((item) => item.category.id === selectedCategoryId.value)?.category || null
  }
  return visibleCategoryItems.value[0]?.category || null
})

async function loadStats() {
  if (!api.getRegistryIndexStats) return
  isStatsLoading.value = true
  try {
    stats.value = await api.getRegistryIndexStats()
  } catch (error) {
    message.error(errorMessage(error, '读取索引统计失败'))
  } finally {
    isStatsLoading.value = false
  }
}

async function loadEntities() {
  if (!api.getRegistryEntities) return
  isTableLoading.value = true
  try {
    entities.value = await api.getRegistryEntities({
      entityType: filters.entityType,
      q: filters.keyword.trim() || null,
      status: filters.status,
      page: filters.page,
      pageSize: filters.pageSize,
      sort: filters.sort,
      order: filters.order
    })
  } catch (error) {
    message.error(errorMessage(error, '读取注册表索引失败'))
  } finally {
    isTableLoading.value = false
  }
}

async function rebuildIndex() {
  if (!api.rebuildRegistryIndex) return
  isSyncing.value = true
  try {
    lastSync.value = await api.rebuildRegistryIndex()
    message.success(lastSync.value.message || '索引重建完成')
    await Promise.all([loadStats(), loadEntities()])
  } catch (error) {
    message.error(errorMessage(error, '重建索引失败'))
  } finally {
    isSyncing.value = false
  }
}

async function syncTagsFromArticles() {
  if (!api.syncTags) return
  isTagSyncing.value = true
  try {
    const result = await api.syncTags({ dryRun: false, confirm: true })
    message.success(`标签同步完成：发现 ${result.discovered_count} 个，新增 ${result.created_tags.length} 个`)
    await Promise.all([loadStats(), loadEntities(), loadYamlWorkspace()])
  } catch (error) {
    message.error(errorMessage(error, '同步文章标签失败'))
  } finally {
    isTagSyncing.value = false
  }
}

async function loadYamlWorkspace() {
  await Promise.all([loadYamlFile(), loadYamlEntries(), loadDiff()])
}

async function loadYamlFile() {
  if (!api.getRegistryYaml) return
  isYamlLoading.value = true
  try {
    yamlFile.value = await api.getRegistryYaml(yamlRegistryType.value)
    yamlContent.value = yamlFile.value.content
  } catch (error) {
    message.error(errorMessage(error, '读取 YAML 原文失败'))
  } finally {
    isYamlLoading.value = false
  }
}

async function loadYamlEntries() {
  if (!api.getRegistryYamlEntries) return
  isYamlLoading.value = true
  try {
    yamlEntries.value = await api.getRegistryYamlEntries(yamlRegistryType.value)
    selectedEntryIndex.value = 0
    syncEntryForm()
  } catch (error) {
    message.error(errorMessage(error, '读取 YAML 条目失败'))
  } finally {
    isYamlLoading.value = false
  }
}

async function saveYamlRaw() {
  if (!api.saveRegistryYaml) return
  isYamlSaving.value = true
  try {
    await api.saveRegistryYaml(yamlRegistryType.value, {
      content: yamlContent.value,
      rebuild_index: true
    })
    message.success('YAML 已保存，索引已重建')
    await Promise.all([loadStats(), loadEntities(), loadYamlWorkspace()])
  } catch (error) {
    message.error(errorMessage(error, '保存 YAML 原文失败'))
  } finally {
    isYamlSaving.value = false
  }
}

async function saveYamlEntryForm() {
  if (!api.saveRegistryYamlEntries || !yamlEntries.value) return
  const items = [...yamlEntries.value.items]
  const nextEntry = buildEntryFromForm(items[selectedEntryIndex.value] || {})
  items[selectedEntryIndex.value] = nextEntry
  await saveYamlEntries(items, 'YAML 条目已保存，索引已重建')
}

async function deleteSelectedEntry() {
  if (!yamlEntries.value) return
  const items = yamlEntries.value.items.filter((_, index) => index !== selectedEntryIndex.value)
  selectedEntryIndex.value = Math.max(0, selectedEntryIndex.value - 1)
  await saveYamlEntries(items, 'YAML 条目已删除，索引已重建')
}

async function addEntry() {
  if (!yamlEntries.value) return
  const items = [...yamlEntries.value.items, defaultEntry()]
  selectedEntryIndex.value = items.length - 1
  await saveYamlEntries(items, 'YAML 条目已新增，索引已重建')
}

async function saveYamlEntries(items: Record<string, unknown>[], successText: string) {
  if (!api.saveRegistryYamlEntries) return
  isYamlSaving.value = true
  try {
    await api.saveRegistryYamlEntries(yamlRegistryType.value, {
      items,
      rebuild_index: true
    })
    message.success(successText)
    await Promise.all([loadStats(), loadEntities(), loadYamlWorkspace()])
  } catch (error) {
    message.error(errorMessage(error, '保存 YAML 条目失败'))
  } finally {
    isYamlSaving.value = false
  }
}

async function loadDiff() {
  if (!api.getRegistryDiff) return
  isDiffLoading.value = true
  try {
    diffResult.value = await api.getRegistryDiff(yamlRegistryType.value)
  } catch (error) {
    message.error(errorMessage(error, '检查差异失败'))
  } finally {
    isDiffLoading.value = false
  }
}

async function loadSidebarStatus() {
  if (!api.getSidebarStatus) return
  isSidebarLoading.value = true
  try {
    sidebarStatus.value = await api.getSidebarStatus(true)
  } catch (error) {
    message.error(errorMessage(error, '读取 docs 侧边栏对账状态失败'))
  } finally {
    isSidebarLoading.value = false
  }
}

async function syncSidebarDocs() {
  if (!api.syncSidebars) return
  isSidebarSyncing.value = true
  try {
    const plan = await api.syncSidebars({ mode: 'append_missing', dryRun: false, confirm: true })
    message.success(`docs 侧边栏已同步：${plan.changes.length} 项变更`)
    await loadSidebarStatus()
  } catch (error) {
    message.error(errorMessage(error, '同步 docs 侧边栏失败'))
  } finally {
    isSidebarSyncing.value = false
  }
}

async function loadDocusaurusStatus() {
  if (!api.getDocusaurusConfigStatus) return
  isDocusaurusLoading.value = true
  try {
    docusaurusStatus.value = await api.getDocusaurusConfigStatus()
  } catch (error) {
    message.error(errorMessage(error, '读取 navbar 对账状态失败'))
  } finally {
    isDocusaurusLoading.value = false
  }
}

async function syncDocusaurusConfigAll() {
  if (!api.syncDocusaurusConfig) return
  isDocusaurusSyncing.value = true
  try {
    const plan = await api.syncDocusaurusConfig({ mode: 'all', dryRun: false, confirm: true })
    message.success(`navbar 已同步：${plan.changes.length} 项变更`)
    await loadDocusaurusStatus()
  } catch (error) {
    message.error(errorMessage(error, '同步 navbar 失败'))
  } finally {
    isDocusaurusSyncing.value = false
  }
}

async function loadCategoryTree() {
  if (!api.getCategories) return
  isCategoryLoading.value = true
  try {
    categoryTree.value = await api.getCategories({
      type: 'docs',
      includeEmpty: true,
      includeCounts: true
    }) as CategoryDTO[]
    syncCategorySelection()
  } catch (error) {
    message.error(errorMessage(error, '读取分类目录失败'))
  } finally {
    isCategoryLoading.value = false
  }
}

async function openRenameCategory(category: CategoryDTO) {
  if (!api.renameCategory) {
    message.warning('当前后端不支持重命名分类接口')
    return
  }
  renameCategoryTarget.value = category
  renameCategoryPlan.value = null
  renameCategoryForm.targetSlug = category.slug
  renameCategoryForm.targetLabel = category.label
  renameCategoryForm.replaceLinks = true
}

async function previewRenameCategory() {
  if (!api.renameCategory || !renameCategoryTarget.value) return
  const targetSlug = renameCategoryForm.targetSlug.trim()
  if (!targetSlug) {
    message.warning('请填写新的分类 slug')
    return
  }
  isCategoryRenamePlanLoading.value = true
  try {
    renameCategoryPlan.value = await api.renameCategory(renameCategoryTarget.value.id, {
      targetSlug,
      targetLabel: renameCategoryForm.targetLabel.trim() || null,
      replaceLinks: renameCategoryForm.replaceLinks,
      dryRun: true,
      confirm: false
    })
  } catch (error) {
    message.error(errorMessage(error, '生成重命名预览失败'))
  } finally {
    isCategoryRenamePlanLoading.value = false
  }
}

async function confirmRenameCategory() {
  if (!api.renameCategory || !renameCategoryTarget.value) return
  const targetSlug = renameCategoryForm.targetSlug.trim()
  if (!targetSlug) {
    message.warning('请填写新的分类 slug')
    return
  }
  isCategoryRenaming.value = true
  try {
    await api.renameCategory(renameCategoryTarget.value.id, {
      targetSlug,
      targetLabel: renameCategoryForm.targetLabel.trim() || null,
      replaceLinks: renameCategoryForm.replaceLinks,
      dryRun: false,
      confirm: true
    })
    message.success('分类及相关文件已重命名')
    closeRenameCategoryModal()
    if (api.rebuildRegistryIndex) {
      await api.rebuildRegistryIndex()
    }
    await Promise.all([loadCategoryTree(), loadStats(), loadEntities(), loadYamlWorkspace()])
  } catch (error) {
    message.error(errorMessage(error, '重命名分类失败'))
  } finally {
    isCategoryRenaming.value = false
  }
}

function closeRenameCategoryModal() {
  renameCategoryTarget.value = null
  renameCategoryPlan.value = null
}

async function openDeleteCategory(category: CategoryDTO) {
  if (!api.deleteCategory) {
    message.warning('当前后端不支持删除分类接口')
    return
  }
  deleteCategoryTarget.value = category
  deleteCategoryPlan.value = null
  await previewDeleteCategory()
}

async function previewDeleteCategory() {
  if (!api.deleteCategory || !deleteCategoryTarget.value) return
  isCategoryPlanLoading.value = true
  try {
    deleteCategoryPlan.value = await api.deleteCategory(deleteCategoryTarget.value.id, {
      dryRun: true,
      confirm: false
    })
  } catch (error) {
    message.error(errorMessage(error, '生成删除预览失败'))
  } finally {
    isCategoryPlanLoading.value = false
  }
}

async function confirmDeleteCategory() {
  if (!api.deleteCategory || !deleteCategoryTarget.value) return
  isCategoryDeleting.value = true
  try {
    await api.deleteCategory(deleteCategoryTarget.value.id, {
      dryRun: false,
      confirm: true
    })
    message.success('分类及相关文件已删除')
    closeDeleteCategoryModal()
    if (api.rebuildRegistryIndex) {
      await api.rebuildRegistryIndex()
    }
    await Promise.all([loadCategoryTree(), loadStats(), loadEntities(), loadYamlWorkspace()])
  } catch (error) {
    message.error(errorMessage(error, '删除分类失败'))
  } finally {
    isCategoryDeleting.value = false
  }
}

function closeDeleteCategoryModal() {
  deleteCategoryTarget.value = null
  deleteCategoryPlan.value = null
}

function selectCategory(category: CategoryDTO) {
  selectedCategoryId.value = category.id
}

function toggleCategory(category: CategoryDTO) {
  const next = new Set(expandedCategoryIds.value)
  if (next.has(category.id)) {
    next.delete(category.id)
  } else {
    next.add(category.id)
  }
  expandedCategoryIds.value = next
}

function expandAllCategories() {
  expandedCategoryIds.value = new Set(allCategoryItems.value.map((item) => item.category.id))
}

function collapseAllCategories() {
  expandedCategoryIds.value = new Set(categoryTree.value.map((category) => category.id))
}

function syncCategorySelection() {
  if (!categoryTree.value.length) {
    selectedCategoryId.value = null
    expandedCategoryIds.value = new Set()
    return
  }

  if (!expandedCategoryIds.value.size) {
    expandedCategoryIds.value = new Set(categoryTree.value.map((category) => category.id))
  }

  if (!selectedCategoryId.value || !allCategoryItems.value.some((item) => item.category.id === selectedCategoryId.value)) {
    selectedCategoryId.value = categoryTree.value[0]?.id || null
  }
}

function handleYamlRegistryChange(value: string) {
  yamlRegistryType.value = value as RegistryType
  loadYamlWorkspace()
}

function selectEntry(index: number) {
  selectedEntryIndex.value = index
  syncEntryForm()
}

function syncEntryForm() {
  const entry = yamlEntries.value?.items[selectedEntryIndex.value] || defaultEntry()
  entryForm.type = String(entry.type || 'docs')
  entryForm.slug = String(entry.slug || '')
  entryForm.pathText = Array.isArray(entry.path) ? entry.path.map(String).join('/') : ''
  entryForm.label = String(entry.label || entry.name || '')
  entryForm.aliases = Array.isArray(entry.aliases) ? entry.aliases.map(String) : []
  entryForm.description = String(entry.description || '')
  entryForm.cover = String(entry.cover || '')
  entryForm.sort_order = typeof entry.sort_order === 'number' ? entry.sort_order : null
  entryForm.enabled = typeof entry.enabled === 'boolean' ? entry.enabled : true
  entryForm.id = String(entry.id || '')
  entryForm.body_path = String(entry.body_path || '')
}

function buildEntryFromForm(original: Record<string, unknown>): Record<string, unknown> {
  if (yamlRegistryType.value === 'categories') {
    return {
      ...original,
      type: entryForm.type,
      slug: entryForm.slug.trim() || lastPathSegment(entryForm.pathText),
      path: entryForm.pathText.split('/').map(part => part.trim()).filter(Boolean),
      label: entryForm.label.trim(),
      aliases: entryForm.aliases,
      description: entryForm.description.trim() || null,
      cover: entryForm.cover.trim() || null,
      sort_order: entryForm.sort_order,
      enabled: entryForm.enabled
    }
  }
  if (yamlRegistryType.value === 'tags') {
    return {
      ...original,
      slug: entryForm.slug.trim(),
      label: entryForm.label.trim(),
      description: entryForm.description.trim() || null
    }
  }
  return original
}

function defaultEntry(): Record<string, unknown> {
  if (yamlRegistryType.value === 'categories') {
    return {
      type: 'docs',
      slug: 'new-category',
      path: ['new-category'],
      label: '新分类',
      aliases: [],
      description: null,
      cover: null,
      sort_order: 10,
      enabled: true
    }
  }
  if (yamlRegistryType.value === 'tags') {
    return {
      slug: 'new-tag',
      label: '新标签',
      description: null
    }
  }
  return {}
}

function yamlEntryKey(entry: Record<string, unknown>): string {
  if (yamlRegistryType.value === 'categories') {
    const type = String(entry.type || 'docs')
    const path = Array.isArray(entry.path) ? entry.path.map(String).join('/') : String(entry.slug || '')
    return `${type}:${path}`
  }
  return String(entry.slug || '')
}

function lastPathSegment(pathText: string): string {
  const parts = pathText.split('/').map(part => part.trim()).filter(Boolean)
  return parts.at(-1) || 'new-category'
}

function handleEntityTypeChange(value: string) {
  filters.entityType = value === '__all' ? null : value as EntityType
  filters.page = 1
  loadEntities()
}

function search() {
  filters.page = 1
  loadEntities()
}

function resetFilters() {
  filters.entityType = 'category'
  filters.keyword = ''
  filters.status = 'active'
  filters.sort = 'updated_at'
  filters.order = 'desc'
  filters.page = 1
  filters.pageSize = 20
  loadEntities()
}

function handlePageChange(page: number) {
  filters.page = page
  loadEntities()
}

function handlePageSizeChange(pageSize: number) {
  filters.pageSize = pageSize
  filters.page = 1
  loadEntities()
}

function entityTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    category: '分类',
    tag: '标签',
    article: '文章'
  }
  return labels[type] || type
}

function sourceKindLabel(kind: string): string {
  const labels: Record<string, string> = {
    yaml: 'YAML',
    markdown: 'Markdown',
    generated: '生成',
    manual: '手动'
  }
  return labels[kind] || kind
}

function tagType(type: string): 'success' | 'info' | 'warning' | 'default' {
  if (type === 'category') return 'success'
  if (type === 'tag') return 'info'
  return 'default'
}

function formatDateTime(value?: string | null): string {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', {
    hour12: false,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function errorMessage(error: unknown, fallback: string): string {
  if (error && typeof error === 'object' && 'message' in error) {
    return String((error as { message?: unknown }).message || fallback)
  }
  return fallback
}

function categoryPath(category: CategoryDTO): string {
  return category.path.join('/') || category.slug
}

function renamedCategoryPath(category: CategoryDTO, targetSlug: string): string {
  const normalizedSlug = targetSlug.trim() || category.slug
  return [...category.path.slice(0, -1), normalizedSlug].join('/') || normalizedSlug
}

function categoryDepthLabel(category: CategoryDTO): string {
  return `${category.path.length} 级分类`
}

function flattenCategoryItems(categories: CategoryDTO[], depth = 0): CategoryListItem[] {
  return categories.flatMap((category) => [
    {
      category,
      depth,
      childCount: category.children?.length || 0
    },
    ...flattenCategoryItems(category.children || [], depth + 1)
  ])
}

function categoryMatches(category: CategoryDTO, keyword: string): boolean {
  return [
    category.label,
    category.slug,
    categoryPath(category)
  ].some((value) => value.toLowerCase().includes(keyword))
}

function hasMatchingDescendant(category: CategoryDTO, keyword: string): boolean {
  return (category.children || []).some(
    (child) => categoryMatches(child, keyword) || hasMatchingDescendant(child, keyword)
  )
}

function formatChange(change: FileChangeDTO): string {
  if (change.from && change.to) {
    return `${change.description}: ${change.from} -> ${change.to}`
  }
  if (change.from || change.to) {
    return `${change.description}: ${change.from || change.to}`
  }
  return `${change.description}: ${change.target}`
}

onMounted(async () => {
  await Promise.all([
    loadStats(),
    loadEntities(),
    loadYamlWorkspace(),
    loadCategoryTree(),
    loadSidebarStatus(),
    loadDocusaurusStatus()
  ])
})
</script>

<template>
  <div class="page-shell registry-page workspace-scroll">
    <header class="registry-header">
      <div>
        <p class="page-kicker">Registry Index</p>
        <h1 class="page-heading">内容注册表</h1>
        <p class="page-subtitle">YAML 和 Markdown 仍是源文件；SQLite 负责后台搜索、分页、排序和统计。</p>
      </div>
      <n-space>
        <n-button :loading="isStatsLoading" @click="loadStats">刷新状态</n-button>
        <n-button type="primary" :loading="isSyncing" @click="rebuildIndex">重建索引</n-button>
      </n-space>
    </header>

    <section class="summary-grid">
      <n-card
        v-for="card in summaryCards"
        :key="card.label"
        class="summary-card"
        :class="`tone-${card.tone}`"
        :bordered="false"
      >
        <n-statistic :label="card.label" :value="card.value" />
      </n-card>
    </section>

    <section class="status-strip surface-panel">
      <div>
        <span class="status-label">SQLite</span>
        <span class="mono status-value">{{ databasePath }}</span>
      </div>
      <div>
        <span class="status-label">最近同步</span>
        <span class="status-value">{{ lastSyncText }}</span>
      </div>
      <div>
        <span class="status-label">同步状态</span>
        <n-tag size="small" :type="stats?.last_sync?.status === 'failed' ? 'error' : 'success'" round>
          {{ stats?.last_sync?.status || 'unknown' }}
        </n-tag>
      </div>
    </section>

    <n-alert type="info" :show-icon="false" class="registry-note">
      SQLite 是查询索引；YAML 是源文件。这里可以查看原文、用表单维护 YAML 条目，并检查 YAML 与 SQLite 的键差异。
    </n-alert>

    <n-tabs v-model:value="activePanel" type="line" animated class="registry-tabs">
      <n-tab-pane name="index" tab="SQLite 索引">
        <section class="registry-toolbar surface-panel">
          <n-select
            :value="filters.entityType || '__all'"
            :options="entityTypeOptions"
            class="toolbar-select"
            @update:value="handleEntityTypeChange"
          />
          <n-input
            v-model:value="filters.keyword"
            clearable
            class="toolbar-search"
            placeholder="搜索标题、显示名、实体键、描述"
            @keyup.enter="search"
          />
          <n-select v-model:value="filters.status" :options="statusOptions" class="toolbar-select" @update:value="search" />
          <n-select v-model:value="filters.sort" :options="sortOptions" class="toolbar-select" @update:value="search" />
          <n-select v-model:value="filters.order" :options="orderOptions" class="toolbar-order" @update:value="search" />
          <n-space>
            <n-button type="primary" @click="search">查询</n-button>
            <n-button @click="resetFilters">重置</n-button>
          </n-space>
        </section>

        <section class="registry-table surface-panel">
          <div class="table-header">
            <div>
              <h2>索引实体</h2>
              <p>{{ entityTypeLabel(filters.entityType || '全部') }} · {{ entities.total }} 条记录</p>
            </div>
          </div>
          <n-data-table
            remote
            :columns="columns"
            :data="entities.items"
            :loading="isTableLoading"
            :pagination="pagination"
            :row-key="row => row.id"
            :bordered="false"
            @update:page="handlePageChange"
            @update:page-size="handlePageSizeChange"
          />
        </section>
      </n-tab-pane>

      <n-tab-pane name="categories" tab="分类目录">
        <section class="category-manager surface-panel">
          <div class="table-header">
            <div>
              <h2>分类目录</h2>
              <p>完整 docs 分类树，包含空目录。先选中分类，再在右侧维护路径或预览删除影响。</p>
            </div>
            <n-space>
              <n-button :loading="isCategoryLoading" @click="loadCategoryTree">刷新分类</n-button>
            </n-space>
          </div>

          <div class="category-workbench">
            <div class="category-browser">
              <div class="category-browser-toolbar">
                <n-input
                  v-model:value="categorySearchValue"
                  clearable
                  placeholder="搜索分类名或路径"
                />
                <div class="category-browser-actions">
                  <n-switch v-model:value="showEmptyCategories" size="small" />
                  <span>空分类</span>
                  <n-button size="small" secondary @click="expandAllCategories">展开</n-button>
                  <n-button size="small" secondary @click="collapseAllCategories">收起</n-button>
                </div>
              </div>

              <div class="category-stats-strip">
                <span>全部 {{ categorySummary.total }}</span>
                <span>空分类 {{ categorySummary.empty }}</span>
                <span>文章引用 {{ categorySummary.articleCount }}</span>
              </div>

              <div class="category-list" :class="{ loading: isCategoryLoading }">
                <button
                  v-for="item in visibleCategoryItems"
                  :key="item.category.id"
                  type="button"
                  class="category-row"
                  :class="{ selected: selectedCategory?.id === item.category.id }"
                  :style="{ '--depth-indent': `${item.depth * 22}px` }"
                  @click="selectCategory(item.category)"
                >
                  <span
                    class="category-toggle"
                    :class="{ hidden: item.childCount === 0 }"
                    @click.stop="toggleCategory(item.category)"
                  >
                    {{ expandedCategoryIds.has(item.category.id) || categorySearchValue ? '⌄' : '›' }}
                  </span>
                  <span class="category-row-main">
                    <span class="category-row-title">{{ item.category.label }}</span>
                    <span class="category-row-path mono">{{ categoryPath(item.category) }}</span>
                  </span>
                  <span class="category-row-meta">
                    <span>{{ item.category.article_count ?? 0 }}</span>
                    <span v-if="item.childCount">{{ item.childCount }} 子项</span>
                  </span>
                </button>
                <n-empty
                  v-if="!isCategoryLoading && visibleCategoryItems.length === 0"
                  description="没有匹配的分类"
                  class="category-empty"
                />
              </div>
            </div>

            <aside class="category-detail-panel">
              <template v-if="selectedCategory">
                <p class="detail-kicker">Selected Category</p>
                <h3>{{ selectedCategory.label }}</h3>
                <code class="detail-path">{{ categoryPath(selectedCategory) }}</code>

                <div class="category-detail-grid">
                  <div>
                    <span>层级</span>
                    <strong>{{ categoryDepthLabel(selectedCategory) }}</strong>
                  </div>
                  <div>
                    <span>文章数</span>
                    <strong>{{ selectedCategory.article_count ?? 0 }}</strong>
                  </div>
                  <div>
                    <span>子分类</span>
                    <strong>{{ selectedCategory.children.length }}</strong>
                  </div>
                  <div>
                    <span>状态</span>
                    <strong>{{ selectedCategory.enabled ? '启用' : '隐藏' }}</strong>
                  </div>
                </div>

                <div class="category-actions">
                  <n-button
                    type="primary"
                    block
                    secondary
                    :disabled="isCategoryLoading"
                    @click="openRenameCategory(selectedCategory)"
                  >
                    重命名分类
                  </n-button>

                  <n-alert type="warning" :bordered="false" class="category-danger-note">
                    删除会移除该目录下文章、图片资源、侧边栏登记和分类注册记录。
                  </n-alert>

                  <n-button
                    type="error"
                    block
                    secondary
                    :disabled="isCategoryLoading"
                    @click="openDeleteCategory(selectedCategory)"
                  >
                    预览并删除分类
                  </n-button>
                </div>
              </template>
              <n-empty v-else description="请选择一个分类" />
            </aside>
          </div>
        </section>
      </n-tab-pane>

      <n-tab-pane name="yaml" tab="YAML 原文">
        <section class="yaml-panel surface-panel">
          <div class="panel-toolbar">
            <n-select
              :value="yamlRegistryType"
              :options="registryOptions"
              class="registry-type-select"
              @update:value="handleYamlRegistryChange"
            />
            <span class="mono panel-path">{{ yamlFile?.path || '-' }}</span>
            <n-space>
              <n-button :loading="isYamlLoading" @click="loadYamlFile">重新读取</n-button>
              <n-button
                v-if="yamlRegistryType === 'tags'"
                :loading="isTagSyncing"
                @click="syncTagsFromArticles"
              >
                同步文章标签
              </n-button>
              <n-popconfirm @positive-click="saveYamlRaw">
                <template #trigger>
                  <n-button type="primary" :loading="isYamlSaving">保存原文</n-button>
                </template>
                保存会覆盖当前 YAML 文件，并自动重建 SQLite 索引。
              </n-popconfirm>
            </n-space>
          </div>
          <n-input
            v-model:value="yamlContent"
            type="textarea"
            class="yaml-editor mono"
            :autosize="{ minRows: 22, maxRows: 34 }"
            placeholder="YAML 原文"
          />
        </section>
      </n-tab-pane>

      <n-tab-pane name="form" tab="表单维护">
        <section class="form-workbench">
          <div class="entry-list surface-panel">
            <div class="panel-toolbar compact">
              <n-select
                :value="yamlRegistryType"
                :options="registryOptions"
                class="registry-type-select"
                @update:value="handleYamlRegistryChange"
              />
              <n-button type="primary" secondary @click="addEntry">新增</n-button>
              <n-button
                v-if="yamlRegistryType === 'tags'"
                :loading="isTagSyncing"
                @click="syncTagsFromArticles"
              >
                同步文章标签
              </n-button>
            </div>
            <n-data-table
              :columns="yamlEntryColumns"
              :data="yamlEntries?.items || []"
              :loading="isYamlLoading"
              :pagination="{ pageSize: 10 }"
              :row-key="(_, index) => index"
              :bordered="false"
            />
          </div>

          <div class="entry-form surface-panel">
            <div class="table-header">
              <div>
                <h2>条目字段</h2>
                <p class="mono">{{ yamlEntryKey(yamlEntries?.items[selectedEntryIndex] || {}) || '新条目' }}</p>
              </div>
              <n-space>
                <n-button :loading="isYamlLoading" @click="loadYamlEntries">刷新</n-button>
                <n-popconfirm @positive-click="deleteSelectedEntry">
                  <template #trigger>
                    <n-button type="error" secondary>删除</n-button>
                  </template>
                  删除当前 YAML 条目并重建索引。
                </n-popconfirm>
                <n-button type="primary" :loading="isYamlSaving" @click="saveYamlEntryForm">保存条目</n-button>
              </n-space>
            </div>

            <n-form label-placement="left" label-width="88" class="yaml-form">
              <template v-if="yamlRegistryType === 'categories'">
                <n-form-item label="类型">
                  <n-select v-model:value="entryForm.type" :options="[{ label: 'docs', value: 'docs' }, { label: 'blog', value: 'blog' }]" />
                </n-form-item>
                <n-form-item label="路径">
                  <n-input v-model:value="entryForm.pathText" placeholder="tech-study/java-interview" />
                </n-form-item>
                <n-form-item label="Slug">
                  <n-input v-model:value="entryForm.slug" />
                </n-form-item>
                <n-form-item label="显示名">
                  <n-input v-model:value="entryForm.label" />
                </n-form-item>
                <n-form-item label="别名">
                  <n-dynamic-tags v-model:value="entryForm.aliases" />
                </n-form-item>
                <n-form-item label="描述">
                  <n-input v-model:value="entryForm.description" type="textarea" :autosize="{ minRows: 2, maxRows: 5 }" />
                </n-form-item>
                <n-form-item label="封面">
                  <n-input v-model:value="entryForm.cover" placeholder="/img/covers/example.svg" />
                </n-form-item>
                <n-form-item label="排序">
                  <n-input-number v-model:value="entryForm.sort_order" />
                </n-form-item>
                <n-form-item label="启用">
                  <n-switch v-model:value="entryForm.enabled" />
                </n-form-item>
              </template>

              <template v-else-if="yamlRegistryType === 'tags'">
                <n-form-item label="Slug">
                  <n-input v-model:value="entryForm.slug" />
                </n-form-item>
                <n-form-item label="显示名">
                  <n-input v-model:value="entryForm.label" />
                </n-form-item>
                <n-form-item label="描述">
                  <n-input v-model:value="entryForm.description" type="textarea" :autosize="{ minRows: 2, maxRows: 5 }" />
                </n-form-item>
              </template>

            </n-form>
          </div>
        </section>
      </n-tab-pane>

      <n-tab-pane name="diff" tab="差异检查">
        <section class="diff-panel surface-panel">
          <div class="panel-toolbar">
            <n-select
              :value="yamlRegistryType"
              :options="registryOptions"
              class="registry-type-select"
              @update:value="handleYamlRegistryChange"
            />
            <n-button
              v-if="yamlRegistryType === 'tags'"
              :loading="isTagSyncing"
              @click="syncTagsFromArticles"
            >
              同步文章标签
            </n-button>
            <n-button type="primary" :loading="isDiffLoading" @click="loadDiff">重新检查</n-button>
          </div>

          <div class="diff-summary">
            <n-statistic label="YAML 键数量" :value="diffResult?.yaml_count || 0" />
            <n-statistic label="SQLite 键数量" :value="diffResult?.sqlite_count || 0" />
            <n-statistic label="YAML 有但 SQLite 缺失" :value="diffResult?.missing_in_sqlite.length || 0" />
            <n-statistic label="SQLite 有但 YAML 缺失" :value="diffResult?.missing_in_yaml.length || 0" />
          </div>

          <div class="diff-lists">
            <div>
              <h3>YAML 有但 SQLite 缺失</h3>
              <div class="diff-list mono">
                <span v-for="item in diffResult?.missing_in_sqlite || []" :key="item">{{ item }}</span>
                <span v-if="!diffResult?.missing_in_sqlite.length" class="empty-line">无差异</span>
              </div>
            </div>
            <div>
              <h3>SQLite 有但 YAML 缺失</h3>
              <div class="diff-list mono">
                <span v-for="item in diffResult?.missing_in_yaml || []" :key="item">{{ item }}</span>
                <span v-if="!diffResult?.missing_in_yaml.length" class="empty-line">无差异</span>
              </div>
            </div>
          </div>
        </section>
      </n-tab-pane>

      <n-tab-pane name="sidebars" tab="docs 侧边栏">
        <section class="diff-panel surface-panel">
          <div class="panel-toolbar">
            <span class="panel-hint">检查 docs 文章是否已登记到 sidebars.ts，可一键追加缺失项（孤儿 ID 需人工核实，不会自动删除）。</span>
            <n-button type="primary" :loading="isSidebarLoading" @click="loadSidebarStatus">重新检查</n-button>
            <n-button
              :loading="isSidebarSyncing"
              :disabled="!sidebarStatus?.missing_in_sidebars.length"
              @click="syncSidebarDocs"
            >
              追加缺失（{{ sidebarStatus?.missing_in_sidebars.length || 0 }}）
            </n-button>
          </div>

          <div class="diff-summary">
            <n-statistic label="docs 文章数" :value="sidebarStatus?.docs_count || 0" />
            <n-statistic label="已登记" :value="sidebarStatus?.registered_count || 0" />
            <n-statistic label="未登记" :value="sidebarStatus?.missing_count || 0" />
            <n-statistic label="孤儿 ID" :value="sidebarStatus?.orphan_count || 0" />
          </div>

          <div class="diff-lists">
            <div>
              <h3>docs 有但 sidebars.ts 缺失</h3>
              <div class="diff-list mono">
                <span v-for="item in sidebarStatus?.missing_in_sidebars || []" :key="item">{{ item }}</span>
                <span v-if="!sidebarStatus?.missing_in_sidebars.length" class="empty-line">无差异</span>
              </div>
            </div>
            <div>
              <h3>sidebars.ts 有但 docs 缺失（孤儿）</h3>
              <div class="diff-list mono">
                <span v-for="item in sidebarStatus?.orphan_sidebar_ids || []" :key="item">{{ item }}</span>
                <span v-if="!sidebarStatus?.orphan_sidebar_ids.length" class="empty-line">无差异</span>
              </div>
            </div>
          </div>
        </section>
      </n-tab-pane>

      <n-tab-pane name="navbar" tab="navbar 配置">
        <section class="diff-panel surface-panel">
          <div class="panel-toolbar">
            <span class="panel-hint">检查 docusaurus.config.ts 的 navbar 内部链接是否指向已存在内容，并补齐缺失的 docs 一级分类入口；自定义页面（/projects、/about）不校验。</span>
            <n-button type="primary" :loading="isDocusaurusLoading" @click="loadDocusaurusStatus">重新检查</n-button>
            <n-button
              :loading="isDocusaurusSyncing"
              :disabled="!docusaurusStatus?.broken_to_links.length && !docusaurusStatus?.docs_top_categories_missing_in_nav.length"
              @click="syncDocusaurusConfigAll"
            >
              一键同步（{{ (docusaurusStatus?.broken_to_links.length || 0) + (docusaurusStatus?.docs_top_categories_missing_in_nav.length || 0) }}）
            </n-button>
          </div>

          <div class="diff-summary">
            <n-statistic label="navbar 项总数" :value="docusaurusStatus?.nav_item_total || 0" />
            <n-statistic label="断链" :value="docusaurusStatus?.broken_to_links.length || 0" />
            <n-statistic label="docs 一级分类" :value="docusaurusStatus?.docs_top_category_total || 0" />
            <n-statistic label="未登记到 navbar" :value="docusaurusStatus?.docs_top_categories_missing_in_nav.length || 0" />
          </div>

          <div class="diff-lists">
            <div>
              <h3>断链导航项（指向已删除内容）</h3>
              <div class="diff-list mono">
                <span v-for="item in docusaurusStatus?.broken_to_links || []" :key="item.to">
                  {{ item.to }}<template v-if="item.label">（{{ item.label }}）</template>
                </span>
                <span v-if="!docusaurusStatus?.broken_to_links.length" class="empty-line">无差异</span>
              </div>
            </div>
            <div>
              <h3>docs 一级分类未登记到知识库 navbar</h3>
              <div class="diff-list mono">
                <span v-for="item in docusaurusStatus?.docs_top_categories_missing_in_nav || []" :key="item.slug">
                  {{ item.slug }}（{{ item.label }}）
                </span>
                <span v-if="!docusaurusStatus?.docs_top_categories_missing_in_nav.length" class="empty-line">无差异</span>
              </div>
            </div>
          </div>
        </section>
      </n-tab-pane>
    </n-tabs>

    <n-modal
      :show="!!renameCategoryTarget"
      preset="card"
      title="重命名分类"
      style="width: min(760px, calc(100vw - 32px));"
      :mask-closable="!isCategoryRenaming"
      @update:show="value => { if (!value) closeRenameCategoryModal() }"
    >
      <template v-if="renameCategoryTarget">
        <div class="category-mutation-summary">
          <span>当前分类</span>
          <strong>{{ renameCategoryTarget.label }}</strong>
          <code>{{ categoryPath(renameCategoryTarget) }}</code>
        </div>

        <n-form label-placement="left" label-width="86" class="rename-category-form">
          <n-form-item label="新 Slug">
            <n-input
              v-model:value="renameCategoryForm.targetSlug"
              placeholder="java-guide"
              :disabled="isCategoryRenaming"
              @keyup.enter="previewRenameCategory"
            />
          </n-form-item>
          <n-form-item label="显示名">
            <n-input
              v-model:value="renameCategoryForm.targetLabel"
              placeholder="Java 指南"
              :disabled="isCategoryRenaming"
            />
          </n-form-item>
          <n-form-item label="同步链接">
            <div class="inline-control">
              <n-switch v-model:value="renameCategoryForm.replaceLinks" :disabled="isCategoryRenaming" />
              <span>同步替换文章内旧链接和顶部导航中命中的旧路由</span>
            </div>
          </n-form-item>
        </n-form>

        <div class="rename-path-preview">
          <span>目标路径</span>
          <code>{{ categoryPath(renameCategoryTarget) }}</code>
          <strong>-></strong>
          <code>{{ renamedCategoryPath(renameCategoryTarget, renameCategoryForm.targetSlug) }}</code>
        </div>

        <div v-if="renameCategoryPlan" class="mutation-plan">
          <h3>影响预览</h3>
          <ul>
            <li v-for="(change, index) in renameCategoryPlan.changes" :key="`${change.target}-${index}`">
              {{ formatChange(change) }}
            </li>
          </ul>
          <p v-if="renameCategoryPlan.changes.length === 0" class="empty-line">没有文件变更。</p>
          <n-alert
            v-for="(warning, index) in renameCategoryPlan.warnings"
            :key="index"
            type="warning"
            :bordered="false"
            class="delete-warning"
          >
            {{ warning }}
          </n-alert>
        </div>
      </template>

      <template #footer>
        <n-space justify="end">
          <n-button :disabled="isCategoryRenaming" @click="closeRenameCategoryModal">取消</n-button>
          <n-button
            :loading="isCategoryRenamePlanLoading"
            :disabled="isCategoryRenaming"
            @click="previewRenameCategory"
          >
            预览影响
          </n-button>
          <n-popconfirm @positive-click="confirmRenameCategory">
            <template #trigger>
              <n-button
                type="primary"
                :loading="isCategoryRenaming"
                :disabled="isCategoryRenamePlanLoading || !renameCategoryPlan"
              >
                确认重命名
              </n-button>
            </template>
            确认重命名该分类并同步相关文件？
          </n-popconfirm>
        </n-space>
      </template>
    </n-modal>

    <n-modal
      :show="!!deleteCategoryTarget"
      preset="card"
      title="删除分类"
      style="width: min(720px, calc(100vw - 32px));"
      :mask-closable="!isCategoryDeleting"
      @update:show="value => { if (!value) closeDeleteCategoryModal() }"
    >
      <div v-if="deleteCategoryTarget" class="delete-category-summary">
        <span>分类</span>
        <strong>{{ deleteCategoryTarget.label }}</strong>
        <code>{{ categoryPath(deleteCategoryTarget) }}</code>
      </div>

      <n-alert type="error" :bordered="false" class="delete-category-alert">
        这是不可恢复的文件删除操作。请先核对影响预览，确认无误后再执行。
      </n-alert>

      <div v-if="deleteCategoryPlan" class="delete-plan">
        <h3>影响预览</h3>
        <ul>
          <li v-for="(change, index) in deleteCategoryPlan.changes" :key="`${change.target}-${index}`">
            {{ formatChange(change) }}
          </li>
        </ul>
        <n-alert
          v-for="(warning, index) in deleteCategoryPlan.warnings"
          :key="index"
          type="warning"
          :bordered="false"
          class="delete-warning"
        >
          {{ warning }}
        </n-alert>
      </div>

      <template #footer>
        <n-space justify="end">
          <n-button :disabled="isCategoryDeleting" @click="closeDeleteCategoryModal">取消</n-button>
          <n-button :loading="isCategoryPlanLoading" :disabled="isCategoryDeleting" @click="previewDeleteCategory">
            重新预览
          </n-button>
          <n-popconfirm @positive-click="confirmDeleteCategory">
            <template #trigger>
              <n-button
                type="error"
                :loading="isCategoryDeleting"
                :disabled="isCategoryPlanLoading || !deleteCategoryPlan"
              >
                确认删除
              </n-button>
            </template>
            确认删除该分类目录及相关文件？
          </n-popconfirm>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<style scoped>
.registry-page {
  min-height: 100vh;
}

.registry-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 20px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 14px;
}

.summary-card {
  position: relative;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.84);
}

.summary-card::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 5px;
  background: var(--summary-tone);
}

.tone-green {
  --summary-tone: #256b52;
}

.tone-blue {
  --summary-tone: #486b86;
}

.tone-amber {
  --summary-tone: #a9662b;
}

.tone-olive {
  --summary-tone: #727443;
}

.status-strip {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(180px, 0.8fr) minmax(120px, 0.5fr);
  gap: 18px;
  padding: 14px 16px;
  margin-bottom: 14px;
  align-items: center;
}

.status-label {
  display: block;
  margin-bottom: 4px;
  color: var(--admin-muted);
  font-size: 12px;
  font-weight: 700;
}

.status-value {
  color: var(--admin-text);
  font-size: 13px;
}

.registry-note {
  margin-bottom: 14px;
}

.registry-tabs {
  margin-top: 4px;
}

.registry-toolbar {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 14px;
  margin-bottom: 14px;
}

.toolbar-select {
  width: 132px;
  flex: 0 0 auto;
}

.toolbar-order {
  width: 92px;
  flex: 0 0 auto;
}

.toolbar-search {
  min-width: 220px;
  flex: 1 1 auto;
}

.registry-table {
  padding: 0 0 12px;
  overflow: hidden;
}

.category-manager {
  padding-bottom: 16px;
  overflow: hidden;
}

.category-workbench {
  display: grid;
  grid-template-columns: minmax(460px, 1fr) minmax(300px, 360px);
  gap: 14px;
  padding: 0 18px 18px;
  align-items: start;
}

.category-browser,
.category-detail-panel {
  min-width: 0;
  border: 1px solid rgba(41, 63, 52, 0.1);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.68);
}

.category-browser {
  overflow: hidden;
}

.category-browser-toolbar {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid rgba(41, 63, 52, 0.08);
  background: rgba(250, 252, 247, 0.78);
}

.category-browser-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--admin-muted);
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.category-stats-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(41, 63, 52, 0.08);
  background: rgba(255, 255, 255, 0.6);
}

.category-stats-strip span {
  padding: 4px 9px;
  color: #40514a;
  background: rgba(37, 107, 82, 0.08);
  border: 1px solid rgba(37, 107, 82, 0.1);
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.category-list {
  max-height: 560px;
  overflow: auto;
  padding: 6px;
  background: rgba(255, 255, 255, 0.48);
}

.category-row {
  width: 100%;
  min-height: 56px;
  display: grid;
  grid-template-columns: 26px minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  padding: 7px 10px 7px calc(8px + var(--depth-indent, 0px));
  color: #26342e;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  text-align: left;
  transition: background-color 0.16s, border-color 0.16s, box-shadow 0.16s;
}

.category-row:hover {
  background: rgba(244, 247, 241, 0.86);
  border-color: rgba(41, 63, 52, 0.08);
}

.category-row.selected {
  background: rgba(37, 107, 82, 0.1);
  border-color: rgba(37, 107, 82, 0.18);
  box-shadow: inset 3px 0 0 rgba(37, 107, 82, 0.72);
}

.category-toggle {
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #53665c;
  border-radius: 7px;
  font-size: 17px;
  line-height: 1;
}

.category-toggle:hover {
  background: rgba(37, 107, 82, 0.1);
  color: #1d563f;
}

.category-toggle.hidden {
  visibility: hidden;
}

.category-row-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.category-row-title {
  overflow: hidden;
  color: #26342e;
  font-size: 14px;
  font-weight: 750;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.category-row-path {
  overflow: hidden;
  color: var(--admin-muted);
  font-size: 12px;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.category-row-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #53665c;
  font-size: 12px;
  font-weight: 700;
}

.category-row-meta span {
  padding: 3px 8px;
  background: rgba(244, 247, 241, 0.96);
  border: 1px solid rgba(41, 63, 52, 0.08);
  border-radius: 999px;
}

.category-empty {
  padding: 40px 0;
}

.category-detail-panel {
  position: sticky;
  top: 14px;
  padding: 16px;
}

.detail-kicker {
  margin: 0 0 5px;
  color: var(--admin-muted);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.category-detail-panel h3 {
  margin: 0;
  color: #26342e;
  font-size: 20px;
  font-weight: 800;
  line-height: 1.3;
}

.detail-path {
  display: block;
  margin-top: 8px;
  padding: 9px 10px;
  color: #40514a;
  background: rgba(244, 247, 241, 0.9);
  border: 1px solid rgba(41, 63, 52, 0.08);
  border-radius: 8px;
  font-size: 12px;
  word-break: break-all;
}

.category-detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin: 14px 0;
}

.category-detail-grid div {
  padding: 10px;
  border: 1px solid rgba(41, 63, 52, 0.08);
  border-radius: 8px;
  background: rgba(250, 252, 247, 0.74);
}

.category-detail-grid span {
  display: block;
  color: var(--admin-muted);
  font-size: 12px;
  font-weight: 700;
}

.category-detail-grid strong {
  display: block;
  margin-top: 4px;
  color: #26342e;
  font-size: 15px;
  font-weight: 800;
}

.category-actions {
  display: grid;
  gap: 12px;
}

.category-danger-note {
  margin: 0 0 12px;
}

.category-mutation-summary,
.delete-category-summary {
  display: grid;
  grid-template-columns: 52px minmax(120px, 0.8fr) minmax(180px, 1fr);
  gap: 10px;
  align-items: center;
  padding: 12px 14px;
  border: 1px solid rgba(41, 63, 52, 0.1);
  border-radius: 10px;
  background: rgba(250, 252, 247, 0.9);
}

.category-mutation-summary span,
.delete-category-summary span {
  color: var(--admin-muted);
  font-size: 12px;
  font-weight: 700;
}

.category-mutation-summary strong,
.delete-category-summary strong {
  color: var(--admin-text);
  font-size: 14px;
}

.category-mutation-summary code,
.delete-category-summary code {
  color: #53665c;
  font-size: 12px;
  word-break: break-all;
}

.rename-category-form {
  margin-top: 14px;
}

.inline-control {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 34px;
  color: #40514a;
  font-size: 13px;
}

.rename-path-preview {
  display: grid;
  grid-template-columns: 68px minmax(0, 1fr) auto minmax(0, 1fr);
  gap: 10px;
  align-items: center;
  padding: 10px 12px;
  border: 1px solid rgba(37, 107, 82, 0.14);
  border-radius: 8px;
  background: rgba(37, 107, 82, 0.06);
}

.rename-path-preview span {
  color: var(--admin-muted);
  font-size: 12px;
  font-weight: 700;
}

.rename-path-preview strong {
  color: #256b52;
}

.rename-path-preview code {
  min-width: 0;
  color: #40514a;
  font-size: 12px;
  word-break: break-all;
}

.delete-category-alert {
  margin-top: 12px;
}

.mutation-plan,
.delete-plan {
  margin-top: 14px;
  padding: 12px 14px;
  border: 1px solid rgba(37, 107, 82, 0.14);
  border-radius: 10px;
  background: rgba(250, 252, 247, 0.9);
}

.delete-plan {
  border-color: rgba(185, 75, 75, 0.14);
  background: rgba(255, 250, 250, 0.9);
}

.mutation-plan h3,
.delete-plan h3 {
  margin: 0 0 8px;
  color: #26342e;
  font-size: 14px;
  font-weight: 700;
}

.mutation-plan ul,
.delete-plan ul {
  margin: 0;
  padding-left: 18px;
  color: #40514a;
  font-size: 13px;
  line-height: 1.7;
}

.delete-warning {
  margin-top: 10px;
}

.table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px 12px;
}

.table-header h2 {
  margin: 0;
  font-size: 17px;
}

.table-header p {
  margin: 4px 0 0;
  color: var(--admin-muted);
  font-size: 13px;
}

.entity-cell {
  min-width: 0;
}

.entity-title {
  color: var(--admin-text);
  font-weight: 700;
}

.entity-key {
  margin-top: 3px;
  color: var(--admin-muted);
  font-size: 12px;
}

.path-text {
  color: #53665c;
  font-size: 12px;
}

.yaml-panel,
.diff-panel {
  padding: 14px;
}

.panel-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.panel-toolbar.compact {
  justify-content: space-between;
}

.registry-type-select {
  width: 190px;
  flex: 0 0 auto;
}

.panel-path {
  min-width: 0;
  flex: 1 1 auto;
  color: var(--admin-muted);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.yaml-editor {
  width: 100%;
}

:deep(.yaml-editor textarea) {
  line-height: 1.62;
}

.form-workbench {
  display: grid;
  grid-template-columns: minmax(280px, 0.9fr) minmax(420px, 1.4fr);
  gap: 14px;
}

.entry-list,
.entry-form {
  min-width: 0;
  overflow: hidden;
}

.entry-list {
  padding: 14px;
}

.entry-form {
  padding-bottom: 16px;
}

.yaml-form {
  padding: 0 18px;
}

.diff-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.diff-summary :deep(.n-statistic) {
  padding: 14px;
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(41, 63, 52, 0.08);
  border-radius: 8px;
}

.diff-lists {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.diff-lists h3 {
  margin: 0 0 8px;
  color: var(--admin-text);
  font-size: 15px;
}

.diff-list {
  min-height: 220px;
  max-height: 420px;
  overflow: auto;
  padding: 12px;
  background: rgba(244, 247, 241, 0.84);
  border: 1px solid rgba(41, 63, 52, 0.09);
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.7;
}

.diff-list span {
  display: block;
}

.empty-line {
  color: var(--admin-muted);
}

@media (max-width: 1100px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .registry-toolbar {
    flex-wrap: wrap;
  }

  .form-workbench,
  .diff-lists,
  .diff-summary {
    grid-template-columns: 1fr;
  }

  .toolbar-search {
    flex-basis: 100%;
    order: -1;
  }
}

@media (max-width: 760px) {
  .registry-header {
    flex-direction: column;
  }

  .summary-grid,
  .status-strip {
    grid-template-columns: 1fr;
  }

  .toolbar-select,
  .toolbar-order {
    width: calc(50% - 5px);
  }
}
</style>
