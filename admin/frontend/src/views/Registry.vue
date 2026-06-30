<script setup lang="ts">
import { computed, h, onMounted, reactive, ref } from 'vue'
import {
  NAlert,
  NButton,
  NCard,
  NDataTable,
  NDynamicTags,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
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
  RegistryIndexItemDTO,
  RegistryIndexListResponseDTO,
  RegistryIndexStatsDTO,
  RegistryIndexSyncResultDTO,
  RegistryDiffDTO,
  RegistryYamlEntriesDTO,
  RegistryYamlFileDTO
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
const yamlRegistryType = ref<RegistryType>('categories')
const yamlFile = ref<RegistryYamlFileDTO | null>(null)
const yamlContent = ref('')
const yamlEntries = ref<RegistryYamlEntriesDTO | null>(null)
const selectedEntryIndex = ref(0)
const diffResult = ref<RegistryDiffDTO | null>(null)

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

onMounted(async () => {
  await Promise.all([loadStats(), loadEntities(), loadYamlWorkspace()])
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
    </n-tabs>
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
