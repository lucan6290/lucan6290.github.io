<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import { useAppStore } from '@/stores/app'
import { formatDate } from '@/utils/postDisplay'
import type { PostInfo, GitSyncStatusDTO, RegistryIndexStatsDTO } from '@/types/api'

const router = useRouter()
const appStore = useAppStore()

const loading = ref(true)
const posts = ref<PostInfo[]>([])
const gitStatus = ref<GitSyncStatusDTO | null>(null)
const registryStats = ref<RegistryIndexStatsDTO | null>(null)

const stats = ref({
  total: 0,
  docs: 0,
  blog: 0,
  errors: 0,
  warnings: 0
})

async function loadData() {
  loading.value = true
  try {
    const [postList, git, registry] = await Promise.allSettled([
      api.getPosts(),
      api.getGitSyncStatus(),
      api.getRegistryIndexStats()
    ])

    if (postList.status === 'fulfilled') {
      posts.value = postList.value
      stats.value.total = postList.value.length
      stats.value.docs = postList.value.filter(p => p.type === 'docs').length
      stats.value.blog = postList.value.filter(p => p.type === 'blog').length
      stats.value.errors = postList.value.filter(p => p.displayStatus === 'error').length
      stats.value.warnings = postList.value.filter(p => p.displayStatus === 'warning').length
    }
    if (git.status === 'fulfilled') gitStatus.value = git.value
    if (registry.status === 'fulfilled') registryStats.value = registry.value
  } catch (e) {
    appStore.showToast('加载数据失败', 'error')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div>
    <div class="main-header">
      <div class="main-header-title">仪表盘</div>
      <div class="main-header-actions">
        <button class="btn btn-secondary btn-sm" @click="loadData">刷新</button>
      </div>
    </div>

    <div class="main-content" v-if="!loading">
      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-card-label">文章总数</div>
          <div class="stat-card-value">{{ stats.total }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-card-label">知识库</div>
          <div class="stat-card-value">{{ stats.docs }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-card-label">博客</div>
          <div class="stat-card-value">{{ stats.blog }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-card-label">校验问题</div>
          <div class="stat-card-value" :style="{ color: stats.errors > 0 ? 'var(--status-error)' : stats.warnings > 0 ? 'var(--status-warning)' : 'var(--text-primary)' }">
            {{ stats.errors + stats.warnings }}
          </div>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
        <!-- 最近文章 -->
        <div class="card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h3 style="font-size: 15px; font-weight: 600;">最近文章</h3>
            <button class="btn btn-ghost btn-sm" @click="router.push('/posts')">查看全部</button>
          </div>
          <div v-if="posts.length === 0" class="empty-state" style="padding: 24px;">
            <div class="empty-state-title">暂无文章</div>
          </div>
          <div v-else style="display: flex; flex-direction: column; gap: 8px;">
            <div
              v-for="post in posts.slice(0, 8)"
              :key="post.id"
              class="list-item"
              @click="router.push(`/editor?id=${encodeURIComponent(post.id)}`)"
            >
              <div class="list-item-icon">
                <span class="badge" :class="post.type === 'blog' ? 'badge-info' : 'badge-success'">{{ post.typeLabel }}</span>
              </div>
              <div class="list-item-content">
                <div class="list-item-title">{{ post.title }}</div>
                <div class="list-item-meta">{{ formatDate(post.lastModified) }} · {{ post.categoryLabel }}</div>
              </div>
              <div class="list-item-actions">
                <span class="badge" :class="post.displayStatus === 'error' ? 'badge-danger' : post.displayStatus === 'warning' ? 'badge-warning' : 'badge-success'">{{ post.displayStatusLabel }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Git 状态 + 注册表 -->
        <div style="display: flex; flex-direction: column; gap: 16px;">
          <div class="card">
            <h3 style="font-size: 15px; font-weight: 600; margin-bottom: 12px;">Git 状态</h3>
            <div v-if="gitStatus" style="display: flex; flex-direction: column; gap: 8px;">
              <div style="display: flex; justify-content: space-between;">
                <span style="color: var(--text-secondary);">分支</span>
                <span style="font-weight: 500;">{{ gitStatus.current_branch || '-' }}</span>
              </div>
              <div style="display: flex; justify-content: space-between;">
                <span style="color: var(--text-secondary);">远端配置</span>
                <span class="badge" :class="gitStatus.remote_url ? 'badge-success' : 'badge-warning'">{{ gitStatus.remote_url ? '已配置' : '未配置' }}</span>
              </div>
              <div v-if="gitStatus.remote_url" style="display: flex; justify-content: space-between;">
                <span style="color: var(--text-secondary);">远端地址</span>
                <span style="font-weight: 500; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 200px;">{{ gitStatus.remote_url }}</span>
              </div>
              <div style="display: flex; justify-content: space-between;">
                <span style="color: var(--text-secondary);">SSH Key</span>
                <span class="badge" :class="gitStatus.has_private_key ? 'badge-success' : 'badge-warning'">{{ gitStatus.has_private_key ? '已生成' : '未生成' }}</span>
              </div>
            </div>
            <div v-else class="empty-state" style="padding: 16px;">
              <div class="empty-state-description">无法获取 Git 状态</div>
            </div>
          </div>

          <div class="card">
            <h3 style="font-size: 15px; font-weight: 600; margin-bottom: 12px;">注册表</h3>
            <div v-if="registryStats" style="display: flex; flex-direction: column; gap: 8px;">
              <div style="display: flex; justify-content: space-between;">
                <span style="color: var(--text-secondary);">文章</span>
                <span style="font-weight: 500;">{{ registryStats.article_count }}</span>
              </div>
              <div style="display: flex; justify-content: space-between;">
                <span style="color: var(--text-secondary);">分类</span>
                <span style="font-weight: 500;">{{ registryStats.category_count }}</span>
              </div>
              <div style="display: flex; justify-content: space-between;">
                <span style="color: var(--text-secondary);">标签</span>
                <span style="font-weight: 500;">{{ registryStats.tag_count }}</span>
              </div>
            </div>
            <div v-else class="empty-state" style="padding: 16px;">
              <div class="empty-state-description">无法获取注册表统计</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-else style="display: flex; align-items: center; justify-content: center; height: 400px;">
      <div class="spinner" style="width: 24px; height: 24px;"></div>
    </div>
  </div>
</template>
