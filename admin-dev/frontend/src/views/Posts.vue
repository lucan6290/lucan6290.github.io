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
import type { PostInfo } from '@/types/api'
import NewPostModal from '@/components/NewPostModal.vue'

const router = useRouter()
const message = useMessage()
const postsStore = usePostsStore()

// 状态
const searchValue = ref('')
const statusFilter = ref<string | null>(null)
const selectedCategory = ref<string[]>([])
const isLoading = ref(false)
const showNewPostModal = ref(false)
const siderCollapsed = ref(false)

// 分类映射
const categoryMap: Record<string, string> = {
  'tech-study': '技术研习',
  'pitfall-review': '踩坑复盘',
  'project-practice': '项目实战',
  'growth-essay': '成长随笔',
  'resource-sharing': '资源分享'
}

// 状态选项
const statusOptions = [
  { label: '全部', value: null },
  { label: '已发布', value: 'published' },
  { label: 'WIP', value: 'wip' },
  { label: '草稿', value: 'draft' }
]

// 计算分类树数据
const treeData = computed<TreeOption[]>(() => {
  // 一级分类 slug → 中文名
  const slugToName: Record<string, string> = {
    'tech-study': '技术研习', 'pitfall-review': '踩坑复盘',
    'project-practice': '项目实战', 'growth-essay': '成长随笔',
    'resource-sharing': '资源分享'
  }

  // 按一级分类 slug + 二级分类 slug 分组，同时记录中文名
  // key: 二级分类 slug, value: { name: 中文名, count: 文章数 }
  const categoryGroups: Record<string, Record<string, { name: string; count: number }>> = {}

  postsStore.posts.forEach((post: any) => {
    const category = post.category || '未分类'
    const subSlug = post.subCategory || ''
    // 从 categories 原始数组取中文二级名
    const subName = post.categories?.[1] || subSlug || '其他'

    if (!categoryGroups[category]) {
      categoryGroups[category] = {}
    }
    if (!categoryGroups[category][subSlug]) {
      categoryGroups[category][subSlug] = { name: subName, count: 0 }
    }
    categoryGroups[category][subSlug].count++
  })

  const tree: TreeOption[] = []

  // 按照固定顺序
  const orderedCategories = ['tech-study', 'pitfall-review', 'project-practice', 'growth-essay', 'resource-sharing']

  orderedCategories.forEach((categoryKey) => {
    const categoryLabel = slugToName[categoryKey] || categoryKey
    const subCategories = categoryGroups[categoryKey]

    if (!subCategories) {
      tree.push({
        key: categoryKey,
        label: `${categoryLabel} (0)`,
        children: []
      })
      return
    }

    const children: TreeOption[] = []
    let totalCount = 0

    Object.entries(subCategories).forEach(([subSlug, { name, count }]) => {
      totalCount += count
      children.push({
        key: subSlug ? `${categoryKey}/${subSlug}` : categoryKey,
        label: `${name} (${count})`
      })
    })

    tree.push({
      key: categoryKey,
      label: `${categoryLabel} (${totalCount})`,
      children
    })
  })

  return tree
})

// 过滤后的文章列表
const filteredPosts = computed(() => {
  let result = postsStore.posts

  // 按分类筛选
  if (selectedCategory.value.length > 0) {
    const category = selectedCategory.value[0]
    if (category.includes('/')) {
      // 二级分类
      const [parentCategory, subCategory] = category.split('/')
      result = result.filter(
        (post) => post.category === parentCategory && post.subCategory === subCategory
      )
    } else {
      // 一级分类
      result = result.filter((post) => post.category === category)
    }
  }

  // 按状态筛选
  if (statusFilter.value) {
    result = result.filter((post) => post.status === statusFilter.value)
  }

  // 按文件名搜索
  if (searchValue.value.trim()) {
    const keyword = searchValue.value.toLowerCase()
    result = result.filter((post) => (post.filename || post.title).toLowerCase().includes(keyword))
  }

  return result
})

// 表格列定义
const columns: DataTableColumns<PostInfo> = [
  {
    title: '文件名',
    key: 'filename',
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
    width: 200,
    render(row: any) {
      const tags = []
      // row.categories 是原始中文数组 [一级, 二级]
      const primaryZh = (row.categories?.[0]) || categoryMap[row.category] || row.category
      const secondaryZh = (row.categories?.[1]) || row.subCategory || ''
      if (row.category) {
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
      const statusMap: Record<string, { type: 'success' | 'warning' | 'default'; label: string }> = {
        published: { type: 'success', label: '已发布' },
        wip: { type: 'warning', label: 'WIP' },
        draft: { type: 'default', label: '草稿' }
      }
      const status = statusMap[row.status] || { type: 'default', label: row.status }
      return h(
        NTag,
        { type: status.type, size: 'small' },
        { default: () => status.label }
      )
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    render(row) {
      return h(NSpace, null, {
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
          :default-expanded-keys="['tech-study', 'pitfall-review', 'project-practice', 'growth-essay', 'resource-sharing']"
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
      <n-layout :content-style="siderCollapsed ? 'padding: 24px 24px 24px 48px' : 'padding: 24px'" style="display: flex; flex-direction: column; overflow: hidden;">
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
          >
            <template #empty>
              <n-empty description="暂无文章" />
            </template>
          </n-data-table>
        </div>
      </n-layout>
    </n-layout>

    <NewPostModal v-model:show="showNewPostModal" />
  </div>
</template>

<style scoped>
.posts-page {
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
  overflow-y: auto;
}

.posts-sider {
  border-right: 1px solid rgba(41, 63, 52, 0.12);
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 10px 0 30px rgba(21, 35, 29, 0.04);
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

.sider-expand-btn {
  position: absolute;
  left: 6px;
  top: 18px;
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
  box-shadow: none;
}

.sider-expand-btn:hover {
  color: rgba(37, 107, 82, 0.92);
  background: rgba(255, 255, 255, 0.96);
  border-color: rgba(37, 107, 82, 0.2);
  box-shadow: var(--admin-shadow-sm);
}

.toolbar {
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
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 3px;
  border: 1px solid rgba(41, 63, 52, 0.1);
  border-radius: 10px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.78), rgba(255, 255, 255, 0.62));
  box-shadow: var(--admin-shadow-md);
}

.table-wrapper :deep(.n-data-table-wrapper) {
  min-height: 100%;
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
}

.table-wrapper :deep(.n-tag) {
  font-size: 12px;
  font-weight: 500;
}

.posts-page :deep(.n-tree-node-content) {
  border-radius: 8px;
  color: #40514a;
  font-size: 13.5px;
  font-weight: 400;
  min-height: 34px;
  line-height: 1.45;
}

.posts-page :deep(.n-tree-node-content--selected) {
  background: rgba(47, 112, 85, 0.12);
  color: var(--admin-brand-dark);
  font-weight: 560;
}

@media (max-width: 900px) {
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
