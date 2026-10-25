<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import {
  NCard,
  NStatistic,
  NGrid,
  NGi,
  NButton,
  NDataTable,
  NTag,
  NH1,
  NP,
  useMessage
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { useRouter } from 'vue-router'
import { usePostsStore } from '@/stores/posts'
import type { PostInfo } from '@/types/api'
import NewPostModal from '@/components/NewPostModal.vue'
import { getPostCategoryLabel, getPostDisplayStatus } from '@/utils/postDisplay'

const router = useRouter()
const message = useMessage()
const postsStore = usePostsStore()

type DashboardView = 'recent' | 'ok' | 'issues' | 'category' | 'month'

// 新建文章弹窗
const showNewPostModal = ref(false)
const activeView = ref<DashboardView>('recent')
const selectedCategoryLabel = ref<string | null>(null)

// 当前日期
const currentDate = computed(() => {
  const now = new Date()
  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  }
  return now.toLocaleDateString('zh-CN', options)
})

// 统计数据
const sortedPosts = computed(() =>
  [...postsStore.posts].sort((a, b) => {
    const dateA = new Date(a.date).getTime()
    const dateB = new Date(b.date).getTime()
    return dateB - dateA
  })
)

const okPosts = computed(() =>
  sortedPosts.value.filter((post) => getPostDisplayStatus(post).value === 'ok')
)
const issuePosts = computed(
  () =>
    sortedPosts.value.filter((post) => getPostDisplayStatus(post).value !== 'ok')
)

const thisMonthPosts = computed(() => {
  const now = new Date()
  const currentYear = now.getFullYear()
  const currentMonth = now.getMonth()

  return sortedPosts.value.filter((post) => {
    const postDate = new Date(post.date)
    return postDate.getFullYear() === currentYear && postDate.getMonth() === currentMonth
  })
})

function getCategoryLabel(post: PostInfo): string {
  return getPostCategoryLabel(post)
}

const categoryGroups = computed(() => {
  const groups = new Map<string, { label: string; count: number; latestDate: number }>()

  for (const post of postsStore.posts) {
    const label = getCategoryLabel(post)
    const latestDate = new Date(post.date).getTime() || 0
    const current = groups.get(label)

    if (current) {
      current.count += 1
      current.latestDate = Math.max(current.latestDate, latestDate)
    } else {
      groups.set(label, {
        label,
        count: 1,
        latestDate
      })
    }
  }

  return [...groups.values()].sort((a, b) => b.count - a.count || b.latestDate - a.latestDate)
})

const okCount = computed(() => okPosts.value.length)
const issueCount = computed(() => issuePosts.value.length)
const categoryCount = computed(() => categoryGroups.value.length)
const thisMonthCount = computed(() => thisMonthPosts.value.length)

// 最近文章（最近 10 篇）
const recentPosts = computed(() => sortedPosts.value.slice(0, 10))

const currentPosts = computed(() => {
  switch (activeView.value) {
    case 'ok':
      return okPosts.value
    case 'issues':
      return issuePosts.value
    case 'category':
      return [...sortedPosts.value]
        .filter((post) => !selectedCategoryLabel.value || getCategoryLabel(post) === selectedCategoryLabel.value)
        .sort((a, b) => {
        const categoryCompare = getCategoryLabel(a).localeCompare(getCategoryLabel(b), 'zh-CN')
        if (categoryCompare !== 0) return categoryCompare
        return new Date(b.date).getTime() - new Date(a.date).getTime()
      })
    case 'month':
      return thisMonthPosts.value
    default:
      return recentPosts.value
  }
})

const listTitle = computed(() => {
  const titleMap: Record<DashboardView, string> = {
    recent: '最近文章',
    ok: '正常文章',
    issues: '待处理文章',
    category: '分类内容',
    month: '本月新增'
  }

  return titleMap[activeView.value]
})

const listHint = computed(() => {
  const hintMap: Record<DashboardView, string> = {
    recent: `按创建日期显示最近 ${recentPosts.value.length} 篇文章`,
    ok: `共 ${okCount.value} 篇校验正常文章`,
    issues: `共 ${issueCount.value} 篇存在校验提醒或错误的文章`,
    category: selectedCategoryLabel.value
      ? `${selectedCategoryLabel.value} 下共 ${currentPosts.value.length} 篇文章`
      : `共 ${categoryCount.value} 个分类，包含 ${postsStore.posts.length} 篇文章`,
    month: `本月新增 ${thisMonthCount.value} 篇文章`
  }

  return hintMap[activeView.value]
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
      return row.filename || row.title
    }
  },
  {
    title: '分类',
    key: 'category',
    width: 150,
    render(row) {
      return getCategoryLabel(row)
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row) {
      const status = getPostDisplayStatus(row)
      return h(NTag, { type: status.tagType, size: 'small' }, { default: () => status.label })
    }
  },
  {
    title: '创建日期',
    key: 'date',
    width: 120,
    render(row) {
      return new Date(row.date).toLocaleDateString('zh-CN')
    }
  }
]

// 点击文章行
const handleRowClick = (row: PostInfo) => {
  router.push(`/editor?file=${encodeURIComponent(row.path)}`)
}

const getRowProps = (row: PostInfo) => ({
  class: 'clickable-post-row',
  tabindex: 0,
  onClick: () => handleRowClick(row),
  onKeydown: (event: KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleRowClick(row)
    }
  }
})

const selectView = (view: DashboardView) => {
  activeView.value = view
  if (view !== 'category') {
    selectedCategoryLabel.value = null
  }
}

const selectCategory = (label: string) => {
  activeView.value = 'category'
  selectedCategoryLabel.value = selectedCategoryLabel.value === label ? null : label
}

// 新建文章
const handleCreatePost = () => {
  showNewPostModal.value = true
}

// 加载数据
onMounted(async () => {
  if (!postsStore.hasCache || postsStore.isCacheExpired) {
    try {
      await postsStore.fetchPosts()
    } catch (error) {
      console.error('加载文章列表失败:', error)
      message.error('加载文章列表失败')
    }
  }
})
</script>

<template>
  <div class="dashboard page-shell">
    <!-- 欢迎区 -->
    <div class="welcome-section glass-panel">
      <div class="welcome-left">
        <p class="page-kicker">Dashboard</p>
        <n-h1 class="welcome-title">
          你好，博主！
        </n-h1>
        <n-p class="welcome-date">{{ currentDate }}</n-p>
        <div class="welcome-meta">
          <span>本月新增 {{ thisMonthCount }} 篇</span>
          <span>{{ issueCount }} 篇待处理</span>
        </div>
      </div>
      <div class="welcome-right">
        <n-button size="large" @click="selectView('recent')">
          最近文章
        </n-button>
        <n-button size="large" @click="router.push('/posts')">
          管理文章
        </n-button>
        <n-button type="primary" size="large" @click="handleCreatePost">
          新建文章
        </n-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <n-grid :x-gap="16" :y-gap="16" :cols="4" responsive="screen" item-responsive>
      <n-gi span="4 m:2 l:1">
        <n-card
          class="stat-card published"
          :class="{ active: activeView === 'ok' }"
          role="button"
          tabindex="0"
          @click="selectView('ok')"
          @keydown.enter="selectView('ok')"
          @keydown.space.prevent="selectView('ok')"
        >
          <span class="stat-mark">正常</span>
          <n-statistic label="正常文章" :value="okCount">
            <template #suffix>
              <span class="stat-unit">篇</span>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi span="4 m:2 l:1">
        <n-card
          class="stat-card draft"
          :class="{ active: activeView === 'issues' }"
          role="button"
          tabindex="0"
          @click="selectView('issues')"
          @keydown.enter="selectView('issues')"
          @keydown.space.prevent="selectView('issues')"
        >
          <span class="stat-mark">处理</span>
          <n-statistic label="待处理文章" :value="issueCount">
            <template #suffix>
              <span class="stat-unit">篇</span>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi span="4 m:2 l:1">
        <n-card
          class="stat-card category"
          :class="{ active: activeView === 'category' }"
          role="button"
          tabindex="0"
          @click="selectView('category')"
          @keydown.enter="selectView('category')"
          @keydown.space.prevent="selectView('category')"
        >
          <span class="stat-mark">分类</span>
          <n-statistic label="分类数量" :value="categoryCount">
            <template #suffix>
              <span class="stat-unit">个</span>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi span="4 m:2 l:1">
        <n-card
          class="stat-card month"
          :class="{ active: activeView === 'month' }"
          role="button"
          tabindex="0"
          @click="selectView('month')"
          @keydown.enter="selectView('month')"
          @keydown.space.prevent="selectView('month')"
        >
          <span class="stat-mark">本月</span>
          <n-statistic label="本月新增" :value="thisMonthCount">
            <template #suffix>
              <span class="stat-unit">篇</span>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 文章内容列表 -->
    <n-card class="recent-posts-card" :title="listTitle">
      <template #header-extra>
        <div class="list-actions">
          <span>{{ listHint }}</span>
          <n-button v-if="activeView !== 'recent'" text type="primary" @click="selectView('recent')">
            返回最近文章
          </n-button>
          <n-button text type="primary" @click="router.push('/posts')">
            查看全部
          </n-button>
        </div>
      </template>

      <div v-if="activeView === 'category'" class="category-breakdown">
        <button
          v-for="category in categoryGroups"
          :key="category.label"
          class="category-chip"
          :class="{ active: selectedCategoryLabel === category.label }"
          type="button"
          @click="selectCategory(category.label)"
        >
          <span>{{ category.label }}</span>
          <strong>{{ category.count }} 篇</strong>
        </button>
      </div>

      <n-data-table
        :columns="columns"
        :data="currentPosts"
        :bordered="false"
        :loading="postsStore.isLoading"
        :row-key="(row: PostInfo) => row.path"
        :row-props="getRowProps"
        class="recent-posts-table"
      />
    </n-card>

    <!-- 新建文章弹窗 -->
    <NewPostModal v-model:show="showNewPostModal" />
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 1400px;
}

.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 22px;
  padding: 28px;
  flex-wrap: wrap;
  gap: 16px;
  position: relative;
  overflow: hidden;
}

.welcome-section::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(120deg, rgba(37, 107, 82, 0.1), transparent 44%),
    linear-gradient(90deg, transparent, rgba(169, 102, 43, 0.08));
  pointer-events: none;
}

.welcome-left {
  flex: 1;
  position: relative;
  z-index: 1;
}

.welcome-title {
  margin: 0 0 8px 0;
  font-size: 30px;
  font-weight: 850;
  line-height: 1.2;
}

.welcome-date {
  margin: 0;
  color: var(--admin-muted);
  font-size: 14px;
}

.welcome-right {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
  z-index: 1;
}

.welcome-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 14px;
}

.welcome-meta span {
  padding: 5px 10px;
  color: #385047;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(31, 52, 43, 0.1);
  border-radius: 999px;
  font-size: 12px;
  font-weight: 750;
}

.stat-card {
  cursor: pointer;
  overflow: hidden;
  position: relative;
  min-height: 128px;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.stat-card::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  background: var(--admin-brand);
}

.stat-card::after {
  content: "";
  position: absolute;
  right: 16px;
  top: 16px;
  width: 46px;
  height: 46px;
  background:
    linear-gradient(135deg, rgba(37, 107, 82, 0.12), rgba(169, 102, 43, 0.08));
  border: 1px solid rgba(37, 107, 82, 0.1);
  border-radius: 12px;
}

.stat-mark {
  position: absolute;
  right: 25px;
  top: 31px;
  z-index: 1;
  color: rgba(21, 35, 29, 0.58);
  font-size: 11px;
  font-weight: 850;
}

.stat-card.published::before {
  background: #2f7055;
}

.stat-card.draft::before {
  background: #b96f2d;
}

.stat-card.category::before {
  background: #47627a;
}

.stat-card.month::before {
  background: #7b6840;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--admin-shadow-md);
  border-color: rgba(37, 107, 82, 0.22);
}

.stat-card:focus-visible {
  outline: 2px solid rgba(37, 107, 82, 0.38);
  outline-offset: 3px;
}

.stat-card.active {
  border-color: rgba(37, 107, 82, 0.32);
  box-shadow: var(--admin-shadow-md);
}

.stat-card.active::after {
  background:
    linear-gradient(135deg, rgba(37, 107, 82, 0.2), rgba(169, 102, 43, 0.12));
}

.stat-card :deep(.n-statistic-value__content) {
  font-size: 32px;
  font-weight: 850;
  color: var(--admin-text);
}

.stat-card :deep(.n-statistic__label) {
  color: var(--admin-muted);
  font-weight: 700;
}

.stat-unit {
  font-size: 14px;
  color: var(--admin-muted);
  margin-left: 4px;
}

.recent-posts-card {
  margin-top: 24px;
  overflow: hidden;
}

.list-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.list-actions span {
  color: var(--admin-muted);
  font-size: 12px;
  font-weight: 400;
}

.category-breakdown {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
  padding: 12px;
  border: 1px solid rgba(41, 63, 52, 0.1);
  border-radius: 10px;
  background: rgba(247, 250, 244, 0.72);
}

.category-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  max-width: 100%;
  padding: 7px 10px;
  color: #40514a;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(41, 63, 52, 0.12);
  border-radius: 999px;
  cursor: pointer;
  font: inherit;
  font-size: 12.5px;
  line-height: 1.35;
  transition: background-color 0.18s, border-color 0.18s, color 0.18s, box-shadow 0.18s;
}

.category-chip:hover,
.category-chip.active {
  color: var(--admin-brand-dark);
  background: rgba(37, 107, 82, 0.1);
  border-color: rgba(37, 107, 82, 0.24);
}

.category-chip:focus-visible {
  outline: 2px solid rgba(37, 107, 82, 0.34);
  outline-offset: 2px;
}

.category-chip span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.category-chip strong {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 600;
}

.recent-posts-table {
  cursor: pointer;
}

.recent-posts-table :deep(.n-data-table-tr:hover) {
  background-color: #f7faf4;
}

.recent-posts-table :deep(.clickable-post-row) {
  cursor: pointer;
}

.recent-posts-table :deep(.clickable-post-row:focus-visible td) {
  outline: 2px solid rgba(37, 107, 82, 0.32);
  outline-offset: -2px;
  background: rgba(47, 112, 85, 0.08);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dashboard {
    padding: 18px;
  }

  .welcome-section {
    flex-direction: column;
    align-items: flex-start;
  }

  .welcome-right {
    width: 100%;
    justify-content: space-between;
  }

  .welcome-title {
    font-size: 24px;
  }
}
</style>
