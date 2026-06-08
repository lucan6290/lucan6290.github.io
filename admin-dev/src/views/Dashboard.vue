<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import {
  NCard,
  NStatistic,
  NGrid,
  NGi,
  NButton,
  NDataTable,
  NSpace,
  NTag,
  NH1,
  NP,
  useMessage
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { useRouter } from 'vue-router'
import { usePostsStore } from '@/stores/posts'
import { useAuthStore } from '@/stores/auth'
import { useModeStore } from '@/stores/mode'
import type { PostInfo } from '@/types/api'
import NewPostModal from '@/components/NewPostModal.vue'

const router = useRouter()
const message = useMessage()
const postsStore = usePostsStore()
const authStore = useAuthStore()
const modeStore = useModeStore()

// 新建文章弹窗
const showNewPostModal = ref(false)

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
const publishedCount = computed(() => postsStore.published.length)
const draftCount = computed(
  () =>
    postsStore.posts.filter((post) => post.status === 'draft' || post.status === 'wip').length
)
const categoryCount = computed(() => {
  const categories = new Set(postsStore.posts.map((post) => post.category))
  return categories.size
})
const thisMonthCount = computed(() => {
  const now = new Date()
  const currentYear = now.getFullYear()
  const currentMonth = now.getMonth()

  return postsStore.posts.filter((post) => {
    const postDate = new Date(post.date)
    return postDate.getFullYear() === currentYear && postDate.getMonth() === currentMonth
  }).length
})

// 最近文章（最近 10 篇）
const recentPosts = computed(() => {
  const sorted = [...postsStore.posts].sort((a, b) => {
    const dateA = new Date(a.date).getTime()
    const dateB = new Date(b.date).getTime()
    return dateB - dateA
  })
  return sorted.slice(0, 10)
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
      return row.subCategory ? `${row.category} / ${row.subCategory}` : row.category
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render(row) {
      const statusMap = {
        published: { text: '已发布', type: 'success' as const },
        draft: { text: '草稿', type: 'warning' as const },
        wip: { text: 'WIP', type: 'info' as const }
      }
      const status = statusMap[row.status]
      return h(NTag, { type: status.type, size: 'small' }, { default: () => status.text })
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
  <div class="dashboard">
    <!-- 欢迎区 -->
    <div class="welcome-section">
      <div class="welcome-left">
        <n-h1 class="welcome-title">
          你好，{{ authStore.user?.name || '博主' }}！
        </n-h1>
        <n-p class="welcome-date">{{ currentDate }}</n-p>
      </div>
      <div class="welcome-right">
        <n-tag :type="modeStore.isOnline ? 'success' : 'warning'" size="large">
          {{ modeStore.isOnline ? '在线模式' : '本地模式' }}
        </n-tag>
        <n-button type="primary" size="large" @click="handleCreatePost">
          新建文章
        </n-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <n-grid :x-gap="16" :y-gap="16" :cols="4" responsive="screen" item-responsive>
      <n-gi span="4 m:2 l:1">
        <n-card class="stat-card">
          <n-statistic label="已发布文章" :value="publishedCount">
            <template #suffix>
              <span class="stat-unit">篇</span>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi span="4 m:2 l:1">
        <n-card class="stat-card">
          <n-statistic label="草稿文章" :value="draftCount">
            <template #suffix>
              <span class="stat-unit">篇</span>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi span="4 m:2 l:1">
        <n-card class="stat-card">
          <n-statistic label="分类数量" :value="categoryCount">
            <template #suffix>
              <span class="stat-unit">个</span>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi span="4 m:2 l:1">
        <n-card class="stat-card">
          <n-statistic label="本月新增" :value="thisMonthCount">
            <template #suffix>
              <span class="stat-unit">篇</span>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 最近文章列表 -->
    <n-card class="recent-posts-card" title="最近文章">
      <n-data-table
        :columns="columns"
        :data="recentPosts"
        :bordered="false"
        :loading="postsStore.isLoading"
        :row-key="(row: PostInfo) => row.path"
        :on-row-click="handleRowClick"
        class="recent-posts-table"
      />
    </n-card>

    <!-- 新建文章弹窗 -->
    <NewPostModal v-model:show="showNewPostModal" />
  </div>
</template>

<style scoped>
.dashboard {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.welcome-left {
  flex: 1;
}

.welcome-title {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
}

.welcome-date {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.welcome-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-card {
  cursor: default;
  transition: box-shadow 0.2s;
}

.stat-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.stat-unit {
  font-size: 14px;
  color: #999;
  margin-left: 4px;
}

.recent-posts-card {
  margin-top: 24px;
}

.recent-posts-table {
  cursor: pointer;
}

.recent-posts-table :deep(.n-data-table-tr:hover) {
  background-color: #f5f7fa;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dashboard {
    padding: 16px;
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