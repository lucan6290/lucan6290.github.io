<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import {
  NLayout,
  NLayoutSider,
  NTree,
  NDataTable,
  NInput,
  NSelect,
  NButton,
  NPopconfirm,
  NModal,
  NForm,
  NFormItem,
  NCheckbox,
  NAlert,
  NSpace,
  NTag,
  NSpin,
  NEmpty,
  useMessage,
  type TreeOption,
  type DataTableColumns
} from 'naive-ui'
import { useRouter } from 'vue-router'
import { usePostsStore } from '@/stores/posts'
import { getAPI } from '@/api/index'
import type { ArticleMoveOptions, MutationPlanDTO, PostInfo } from '@/types/api'
import NewPostModal from '@/components/NewPostModal.vue'
import {
  getPostCategoryLabel,
  getPostDisplayStatus,
  getPostPrimaryCategoryKey,
  getPostPrimaryCategoryLabel,
  getPostSecondaryCategoryKey,
  getPostSecondaryCategoryLabel
} from '@/utils/postDisplay'

const router = useRouter()
const message = useMessage()
const postsStore = usePostsStore()

// 状态
const searchValue = ref('')
const statusFilter = ref<string | null>(null)
const selectedCategory = ref<string[]>([])
const isLoading = ref(false)
const showNewPostModal = ref(false)
const showRenameModal = ref(false)
const isRenamePlanning = ref(false)
const isRenaming = ref(false)
const renameSource = ref<PostInfo | null>(null)
const renamePlan = ref<MutationPlanDTO | null>(null)
const renameForm = ref({
  targetSlug: '',
  targetCategoryPathText: '',
  replaceLinks: true
})
const siderCollapsed = ref(false)

const typeOrder = ['docs', 'blog']
const rootCategoryKey = '__root'

// 状态选项
const statusOptions = [
  { label: '全部', value: null },
  { label: '正常', value: 'ok' },
  { label: '有提醒', value: 'warning' },
  { label: '需处理', value: 'error' }
]

function getArticleType(post: PostInfo): 'docs' | 'blog' {
  if (post.type === 'blog') return 'blog'
  return 'docs'
}

function getTypeLabel(type: string): string {
  return type === 'blog' ? '博客' : type === 'docs' ? '知识库' : type
}

function getFileStem(post: PostInfo): string {
  return post.filename || post.relativePath?.split('/').pop()?.replace(/\.[^.]+$/, '') || post.title
}

function getRenameDefaultSlug(post: PostInfo): string {
  if (getArticleType(post) === 'blog') {
    return post.slug || getFileStem(post).replace(/^\d{4}-\d{2}-\d{2}-/, '')
  }
  return getFileStem(post)
}

function parseCategoryPathText(value: string): string[] {
  return value
    .split('/')
    .map((item) => item.trim())
    .filter(Boolean)
}

function buildMoveOptions(post: PostInfo, options?: { dryRun?: boolean; confirm?: boolean }): ArticleMoveOptions {
  const targetType = getArticleType(post)
  return {
    targetType,
    targetSlug: renameForm.value.targetSlug.trim(),
    targetCategoryPath: targetType === 'docs' ? parseCategoryPathText(renameForm.value.targetCategoryPathText) : [],
    replaceLinks: renameForm.value.replaceLinks,
    dryRun: options?.dryRun ?? true,
    confirm: options?.confirm ?? false
  }
}

function formatPlanChange(change: MutationPlanDTO['changes'][number]): string {
  if (change.from && change.to) {
    return `${change.description}: ${change.from} -> ${change.to}`
  }
  if (change.from || change.to) {
    return `${change.description}: ${change.from || change.to}`
  }
  return `${change.description}: ${change.target}`
}

function isRootCategory(post: PostInfo): boolean {
  return !(post.categoryPath && post.categoryPath.length > 0)
}

function getPrimaryLabel(post: PostInfo, rootFallback = '未分类'): string {
  if (isRootCategory(post)) return rootFallback
  return getPostPrimaryCategoryLabel(post)
}

function getSecondaryLabel(post: PostInfo, fallback = ''): string {
  const label = getPostSecondaryCategoryLabel(post)
  return label === '根目录' ? fallback : label
}

function compareCategoryKeys(a: string, b: string): number {
  return a.localeCompare(b, 'zh-CN')
}

// 计算分类树数据
const treeData = computed<TreeOption[]>(() => {
  const typeGroups: Record<string, {
    count: number
    categories: Record<string, {
      label: string
      count: number
      children: Record<string, { label: string; count: number }>
    }>
  }> = {}

  postsStore.posts.forEach((post) => {
    const articleType = getArticleType(post)
    const category = isRootCategory(post) ? rootCategoryKey : getPostPrimaryCategoryKey(post)
    const subSlug = getPostSecondaryCategoryKey(post)
    const subName = getSecondaryLabel(post)

    if (!typeGroups[articleType]) {
      typeGroups[articleType] = {
        count: 0,
        categories: {}
      }
    }
    if (!typeGroups[articleType].categories[category]) {
      typeGroups[articleType].categories[category] = {
        label: getPrimaryLabel(post),
        count: 0,
        children: {}
      }
    }
    typeGroups[articleType].count++
    typeGroups[articleType].categories[category].count++
    if (subSlug) {
      if (!typeGroups[articleType].categories[category].children[subSlug]) {
        typeGroups[articleType].categories[category].children[subSlug] = { label: subName || subSlug, count: 0 }
      }
      typeGroups[articleType].categories[category].children[subSlug].count++
    }
  })

  return Object.entries(typeGroups)
    .sort(([a], [b]) => typeOrder.indexOf(a) - typeOrder.indexOf(b))
    .map(([typeKey, typeGroup]) => ({
      key: `type:${typeKey}`,
      label: `${getTypeLabel(typeKey)} (${typeGroup.count})`,
      children: Object.entries(typeGroup.categories)
        .sort(([a], [b]) => compareCategoryKeys(a, b))
        .map(([categoryKey, group]) => {
          const children = Object.entries(group.children)
            .sort(([, a], [, b]) => a.label.localeCompare(b.label, 'zh-CN'))
            .map(([subSlug, child]) => ({
              key: `type:${typeKey}/category:${categoryKey}/sub:${subSlug || rootCategoryKey}`,
              label: `${child.label} (${child.count})`
            }))
          return {
            key: `type:${typeKey}/category:${categoryKey}`,
            label: `${group.label} (${group.count})`,
            children: children.length > 0 ? children : undefined
          }
        })
    }))
})

const defaultExpandedKeys = computed(() => {
  const keys: string[] = []
  treeData.value.forEach((typeNode) => {
    keys.push(String(typeNode.key))
    typeNode.children?.forEach((categoryNode) => keys.push(String(categoryNode.key)))
  })
  return keys
})

// 过滤后的文章列表
const filteredPosts = computed(() => {
  let result = postsStore.posts

  // 按分类筛选
  if (selectedCategory.value.length > 0) {
    const key = selectedCategory.value[0]
    const typeMatch = key.match(/^type:([^/]+)/)
    const categoryMatch = key.match(/\/category:([^/]+)/)
    const subMatch = key.match(/\/sub:([^/]+)/)
    const selectedType = typeMatch?.[1]
    const selectedCategoryKey = categoryMatch?.[1]
    const selectedSubCategoryKey = subMatch?.[1]

    if (selectedType) {
      result = result.filter((post) => getArticleType(post) === selectedType)
    }
    if (selectedCategoryKey) {
      result = result.filter((post) => {
        const categoryKey = isRootCategory(post) ? rootCategoryKey : getPostPrimaryCategoryKey(post)
        return categoryKey === selectedCategoryKey
      })
    }
    if (selectedSubCategoryKey) {
      const normalizedSubCategory = selectedSubCategoryKey === rootCategoryKey ? '' : selectedSubCategoryKey
      result = result.filter((post) => getPostSecondaryCategoryKey(post) === normalizedSubCategory)
    }
  }

  // 按状态筛选
  if (statusFilter.value) {
    result = result.filter((post) => getPostDisplayStatus(post).value === statusFilter.value)
  }

  // 按文件名搜索
  if (searchValue.value.trim()) {
    const keyword = searchValue.value.toLowerCase()
    result = result.filter((post) =>
      (post.filename || post.title).toLowerCase().includes(keyword) ||
      post.title.toLowerCase().includes(keyword) ||
      getPostCategoryLabel(post).toLowerCase().includes(keyword) ||
      post.tags.some((tag) => tag.toLowerCase().includes(keyword))
    )
  }

  return result
})

// 表格列定义
const columns: DataTableColumns<PostInfo> = [
  {
    title: '文件名',
    key: 'filename',
    width: 320,
    minWidth: 260,
    fixed: 'left',
    ellipsis: {
      tooltip: true
    },
    render(row) {
      return h(
        NButton,
        {
          text: true,
          type: 'primary',
          onClick: () => handleEdit(row)
        },
        { default: () => row.filename || row.title }
      )
    }
  },
  {
    title: '分类',
    key: 'categories',
    width: 180,
    render(row) {
      const tags = []
      const typeZh = getTypeLabel(getArticleType(row))
      const primaryZh = getPrimaryLabel(row, typeZh)
      const secondaryZh = getSecondaryLabel(row)
      tags.push(
        h(
          NTag,
          { type: 'success', size: 'small', style: { marginRight: '4px' } },
          { default: () => typeZh }
        )
      )
      if (!isRootCategory(row) && primaryZh !== typeZh) {
        tags.push(
          h(
            NTag,
            { type: 'info', size: 'small', style: { marginRight: '4px' } },
            { default: () => primaryZh }
          )
        )
      }
      if (secondaryZh) {
        tags.push(
          h(
            NTag,
            { type: 'default', size: 'small' },
            { default: () => secondaryZh }
          )
        )
      }
      return tags
    }
  },
  {
    title: '标签',
    key: 'tags',
    width: 200,
    render(row) {
      if (!row.tags || row.tags.length === 0) return '-'
      return row.tags.map((tag) =>
        h(
          NTag,
          { size: 'small', style: { marginRight: '4px' } },
          { default: () => tag }
        )
      )
    }
  },
  {
    title: '日期',
    key: 'date',
    width: 180,
    render(row) {
      return new Date(row.date).toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row) {
      const status = getPostDisplayStatus(row)
      return h(
        NTag,
        { type: status.tagType, size: 'small' },
        { default: () => status.label }
      )
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 132,
    fixed: 'right',
    align: 'center',
    render(row) {
      return h(NSpace, { vertical: true, size: 6, align: 'center', class: 'table-actions' }, {
        default: () => [
          h(
            NButton,
            {
              size: 'small',
              onClick: () => handleEdit(row)
            },
            { default: () => '编辑' }
          ),
          h(
            NButton,
            {
              size: 'small',
              secondary: true,
              onClick: () => openRenameModal(row)
            },
            { default: () => '重命名' }
          ),
          h(
            NPopconfirm,
            {
              onPositiveClick: () => handleDelete(row)
            },
            {
              trigger: () =>
                h(
                  NButton,
                  { size: 'small', type: 'error' },
                  { default: () => '删除' }
                ),
              default: () => '确定要删除这篇文章吗？'
            }
          )
        ]
      })
    }
  }
]

// 处理分类树选择
const handleTreeSelect = (keys: Array<string | number>) => {
  selectedCategory.value = keys.map(String)
}

// 处理编辑
const handleEdit = (post: PostInfo) => {
  router.push(`/editor?file=${post.path}`)
}

function openRenameModal(post: PostInfo) {
  renameSource.value = post
  renameForm.value = {
    targetSlug: getRenameDefaultSlug(post),
    targetCategoryPathText: (post.categoryPath || []).join('/'),
    replaceLinks: true
  }
  renamePlan.value = null
  showRenameModal.value = true
}

function closeRenameModal() {
  showRenameModal.value = false
  renameSource.value = null
  renamePlan.value = null
}

async function previewRename() {
  const post = renameSource.value
  if (!post) return
  if (!apiSupportsMove()) return
  if (!renameForm.value.targetSlug.trim()) {
    message.warning('请填写新文件名')
    return
  }

  try {
    isRenamePlanning.value = true
    renamePlan.value = await getAPI().movePost!(post.path, buildMoveOptions(post, { dryRun: true }))
  } catch (error) {
    console.error('重命名预览失败:', error)
    message.error(error instanceof Error ? error.message : '重命名预览失败')
  } finally {
    isRenamePlanning.value = false
  }
}

async function confirmRename() {
  const post = renameSource.value
  if (!post) return
  if (!apiSupportsMove()) return
  if (!renameForm.value.targetSlug.trim()) {
    message.warning('请填写新文件名')
    return
  }

  try {
    isRenaming.value = true
    if (!renamePlan.value) {
      renamePlan.value = await getAPI().movePost!(post.path, buildMoveOptions(post, { dryRun: true }))
    }
    await getAPI().movePost!(post.path, buildMoveOptions(post, { dryRun: false, confirm: true }))
    await postsStore.refreshPosts()
    message.success('文章文件名已修改并同步相关文件')
    closeRenameModal()
  } catch (error) {
    console.error('重命名文章失败:', error)
    message.error(error instanceof Error ? error.message : '重命名失败')
  } finally {
    isRenaming.value = false
  }
}

function apiSupportsMove(): boolean {
  if (!getAPI().movePost) {
    message.warning('当前后端不支持文章重命名接口')
    return false
  }
  return true
}

// 处理删除
const handleDelete = async (post: PostInfo) => {
  try {
    isLoading.value = true
    const api = getAPI()

    // 调用 API 删除文章
    await api.deletePost(post.path, post.sha)

    // 从缓存中移除
    postsStore.removePostFromCache(post.path)

    message.success('删除成功')
  } catch (error) {
    console.error('删除文章失败:', error)
    message.error(error instanceof Error ? error.message : '删除失败')
  } finally {
    isLoading.value = false
  }
}

// 加载文章列表
const loadPosts = async () => {
  try {
    isLoading.value = true
    await postsStore.fetchPosts()
  } catch (error) {
    console.error('加载文章列表失败:', error)
    message.error(error instanceof Error ? error.message : '加载失败')
  } finally {
    isLoading.value = false
  }
}

// 初始化
onMounted(() => {
  loadPosts()
})
</script>

<template>
  <div class="posts-page">
    <n-layout has-sider>
      <!-- 左侧分类树 -->
      <n-layout-sider
        bordered
        :width="240"
        :collapsed-width="0"
        :collapsed="siderCollapsed"
        :native-scrollbar="false"
        content-style="padding: 20px 16px;"
        class="posts-sider"
      >
        <div class="sider-header">
          <div>
            <p class="page-kicker">Library</p>
            <h3>分类目录</h3>
          </div>
          <n-button
            text
            size="tiny"
            class="posts-sider-toggle"
            title="收起侧栏"
            @click="siderCollapsed = true"
          >
            ‹
          </n-button>
        </div>
        <n-tree
          :data="treeData"
          :default-expanded-keys="defaultExpandedKeys"
          selectable
          block-line
          @update:selected-keys="handleTreeSelect"
        />
      </n-layout-sider>

      <!-- 展开按钮（侧栏折叠时显示） -->
      <div
        v-if="siderCollapsed"
        class="sider-expand-btn"
        title="展开分类目录"
        @click="siderCollapsed = false"
      >
        ›
      </div>

      <!-- 右侧文章列表 -->
      <n-layout
        class="posts-content"
        content-style="padding: 24px"
        style="display: flex; flex-direction: column; overflow: hidden;"
      >
        <!-- 工具栏 -->
        <div class="toolbar glass-panel">
          <div class="toolbar-title">
            <h2>文章管理</h2>
            <span>{{ filteredPosts.length }} / {{ postsStore.posts.length }} 篇文章</span>
          </div>
          <n-space class="toolbar-filters">
            <n-input
              v-model:value="searchValue"
              placeholder="搜索文章标题..."
              clearable
              style="width: 320px"
            />
            <n-select
              v-model:value="statusFilter"
              :options="statusOptions"
              placeholder="状态筛选"
              clearable
              style="width: 120px"
            />
          </n-space>
          <div class="toolbar-actions">
            <n-button @click="loadPosts">
              刷新
            </n-button>
            <n-button type="primary" @click="showNewPostModal = true">
              新建文章
            </n-button>
          </div>
        </div>

        <!-- 文章列表 -->
        <div class="table-wrapper">
          <n-data-table
            :columns="columns"
            :data="filteredPosts"
            :bordered="false"
            :loading="isLoading"
            :pagination="false"
            :scroll-x="1160"
          >
            <template #empty>
              <n-empty description="暂无文章" />
            </template>
          </n-data-table>
        </div>
      </n-layout>
    </n-layout>

    <NewPostModal v-model:show="showNewPostModal" />

    <n-modal
      v-model:show="showRenameModal"
      preset="card"
      title="修改文章文件名"
      class="rename-modal"
      style="width: min(680px, calc(100vw - 32px));"
      :mask-closable="!isRenaming"
      @after-leave="closeRenameModal"
    >
      <n-form v-if="renameSource" label-placement="left" label-width="104">
        <n-form-item label="当前文件">
          <div class="rename-current">
            <strong>{{ renameSource.filename }}</strong>
            <span>{{ renameSource.relativePath || renameSource.fullPath }}</span>
          </div>
        </n-form-item>
        <n-form-item label="新文件名">
          <n-input
            v-model:value="renameForm.targetSlug"
            placeholder="输入新的文件名，不需要 .md 后缀"
            clearable
            @update:value="renamePlan = null"
          />
        </n-form-item>
        <n-form-item v-if="getArticleType(renameSource) === 'docs'" label="分类路径">
          <n-input
            v-model:value="renameForm.targetCategoryPathText"
            placeholder="例如：项目实战/开发规范；留空表示 docs 根目录"
            clearable
            @update:value="renamePlan = null"
          />
        </n-form-item>
        <n-form-item label="同步链接">
          <n-checkbox
            v-model:checked="renameForm.replaceLinks"
            @update:checked="renamePlan = null"
          >
            同步替换其他文章中的旧链接
          </n-checkbox>
        </n-form-item>
      </n-form>

      <n-alert type="info" :bordered="false" class="rename-note">
        确认后会移动文章文件；如存在同名图片目录，也会同步移动并更新正文图片引用。知识库文章还会同步替换 sidebars.ts 中的文档 ID。
      </n-alert>

      <div v-if="renamePlan" class="rename-plan">
        <h4>影响预览</h4>
        <ul>
          <li v-for="(change, index) in renamePlan.changes" :key="`${change.target}-${index}`">
            {{ formatPlanChange(change) }}
          </li>
        </ul>
        <n-alert
          v-for="(warning, index) in renamePlan.warnings"
          :key="index"
          type="warning"
          :bordered="false"
          class="rename-warning"
        >
          {{ warning }}
        </n-alert>
      </div>

      <template #footer>
        <n-space justify="end">
          <n-button :disabled="isRenaming" @click="closeRenameModal">
            取消
          </n-button>
          <n-button :loading="isRenamePlanning" :disabled="isRenaming" @click="previewRename">
            预览影响
          </n-button>
          <n-button type="primary" :loading="isRenaming" :disabled="isRenamePlanning" @click="confirmRename">
            确认修改
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<style scoped>
.posts-page {
  --posts-right-safe-space: 36px;
  height: 100%;
  overflow: hidden;
  position: relative;
}

.posts-page :deep(.n-layout) {
  height: 100%;
}

.posts-page :deep(.n-layout-content) {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.posts-page :deep(.n-layout-sider) {
  height: 100%;
}

.posts-sider {
  position: relative;
  border-right: 1px solid rgba(41, 63, 52, 0.12);
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 10px 0 30px rgba(21, 35, 29, 0.04);
  overflow: visible;
}

.sider-header {
  margin-bottom: 18px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.sider-header h3 {
  margin: 0;
  color: #26342e;
  font-size: 17px;
  font-weight: 650;
  letter-spacing: 0;
}

.posts-sider-toggle {
  width: 24px;
  height: 28px;
  padding: 0;
  color: rgba(41, 63, 52, 0.48);
  background: rgba(255, 255, 255, 0.42);
  border: 1px solid transparent;
  border-radius: 8px;
  font-size: 18px;
  line-height: 1;
  transition: background-color 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
}

.posts-sider-toggle:hover {
  color: rgba(37, 107, 82, 0.92);
  background: rgba(255, 255, 255, 0.96);
  border-color: rgba(37, 107, 82, 0.2);
  box-shadow: var(--admin-shadow-sm);
}

.posts-sider :deep(.n-tree) {
  padding: 4px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.48);
}

.posts-content {
  min-width: 0;
}

.sider-expand-btn {
  position: absolute;
  left: 8px;
  top: 36px;
  width: 24px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.42);
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  color: rgba(41, 63, 52, 0.48);
  font-size: 18px;
  line-height: 1;
  z-index: 10;
  transition: background-color 0.2s, border-color 0.2s, color 0.2s, box-shadow 0.2s;
}

.sider-expand-btn:hover {
  color: rgba(37, 107, 82, 0.92);
  background: rgba(255, 255, 255, 0.96);
  border-color: rgba(37, 107, 82, 0.2);
  box-shadow: var(--admin-shadow-sm);
}

.toolbar {
  width: calc(100% - var(--posts-right-safe-space));
  max-width: calc(100% - var(--posts-right-safe-space));
  box-sizing: border-box;
  margin-bottom: 16px;
  padding: 16px 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  gap: 14px;
}

.toolbar-filters {
  flex: 1;
  justify-content: flex-end;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar-title h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 620;
  line-height: 1.28;
  letter-spacing: 0;
}

.toolbar-title span {
  display: block;
  margin-top: 3px;
  color: var(--admin-muted);
  font-size: 12px;
  font-weight: 500;
}

.table-wrapper {
  width: calc(100% - var(--posts-right-safe-space));
  flex: 1;
  max-width: calc(100% - var(--posts-right-safe-space));
  min-height: 0;
  overflow: auto;
  padding: 3px;
  box-sizing: border-box;
  border: 1px solid rgba(41, 63, 52, 0.1);
  border-radius: 10px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.78), rgba(255, 255, 255, 0.62));
  box-shadow: var(--admin-shadow-md);
}

.table-wrapper :deep(.n-data-table-wrapper) {
  min-height: 100%;
}

.table-wrapper :deep(.n-data-table-th--fixed-right),
.table-wrapper :deep(.n-data-table-td--fixed-right) {
  background: rgba(255, 255, 255, 0.96);
}

.table-wrapper :deep(.table-actions) {
  width: 100%;
}

.table-wrapper :deep(.n-data-table-th) {
  font-size: 13px;
  font-weight: 560;
  letter-spacing: 0;
}

.table-wrapper :deep(.n-data-table-td) {
  color: #26342e;
  font-size: 13.5px;
  font-weight: 400;
  line-height: 1.55;
}

.table-wrapper :deep(.n-button) {
  font-weight: 500;
}

.table-wrapper :deep(.n-button--primary-type.n-button--text-type) {
  font-weight: 520;
  max-width: 100%;
}

.table-wrapper :deep(.n-tag) {
  font-size: 12px;
  font-weight: 500;
}

.posts-page :deep(.n-tree-node-content) {
  display: flex;
  align-items: center;
  border-radius: 8px;
  color: #40514a;
  font-size: 13.5px;
  font-weight: 400;
  min-height: 34px;
  line-height: 1.45;
}

.posts-page :deep(.n-tree-node-switcher) {
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.posts-page :deep(.n-tree-node-switcher__icon) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transform-origin: center;
}

.posts-page :deep(.n-tree-node-content__text) {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
}

.posts-page :deep(.n-tree-node-content--selected) {
  background: rgba(47, 112, 85, 0.12);
  color: var(--admin-brand-dark);
  font-weight: 560;
}

.rename-current {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: #26342e;
}

.rename-current strong {
  font-size: 14px;
  font-weight: 650;
}

.rename-current span {
  color: var(--admin-muted);
  font-size: 12px;
  word-break: break-all;
}

.rename-note {
  margin-top: 4px;
}

.rename-plan {
  margin-top: 14px;
  padding: 12px 14px;
  border: 1px solid rgba(41, 63, 52, 0.1);
  border-radius: 10px;
  background: rgba(250, 252, 247, 0.92);
}

.rename-plan h4 {
  margin: 0 0 8px;
  color: #26342e;
  font-size: 14px;
  font-weight: 650;
}

.rename-plan ul {
  margin: 0;
  padding-left: 18px;
  color: #40514a;
  font-size: 13px;
  line-height: 1.7;
}

.rename-warning {
  margin-top: 10px;
}

@media (max-width: 900px) {
  .posts-page {
    --posts-right-safe-space: 0px;
  }

  .toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .toolbar-filters,
  .toolbar-actions {
    width: 100%;
    justify-content: flex-start;
  }
}

@media (max-width: 760px) {
  .posts-sider,
  .sider-expand-btn {
    display: none;
  }

  .posts-page :deep(.n-layout-content) {
    padding: 16px !important;
  }

  .toolbar-filters :deep(.n-input),
  .toolbar-filters :deep(.n-select) {
    width: 100% !important;
  }
}
</style>
