<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import { useAppStore } from '@/stores/app'
import { formatDateTime } from '@/utils/postDisplay'
import type { RegistryIndexStatsDTO, RegistryIndexListResponseDTO, RegistryIndexSyncResultDTO } from '@/types/api'

const appStore = useAppStore()

const loading = ref(true)
const syncing = ref(false)
const stats = ref<RegistryIndexStatsDTO | null>(null)
const entities = ref<RegistryIndexListResponseDTO | null>(null)
const activeTab = ref<'all' | 'category' | 'tag' | 'article'>('all')
const searchTerm = ref('')
const currentPage = ref(1)

function entityTypeLabel(type: string): string {
  const labels: Record<string, string> = { category: '分类', tag: '标签', article: '文章' }
  return labels[type] || type
}

function sourceKindLabel(kind: string): string {
  const labels: Record<string, string> = { yaml: 'YAML', markdown: 'Markdown', generated: '生成', manual: '手动' }
  return labels[kind] || kind
}

async function loadData() {
  loading.value = true
  try {
    const [statsRes, entitiesRes] = await Promise.allSettled([
      api.getRegistryIndexStats(),
      api.getRegistryEntities({
        entityType: activeTab.value === 'all' ? undefined : activeTab.value,
        q: searchTerm.value || undefined,
        page: currentPage.value,
        pageSize: 20
      })
    ])
    if (statsRes.status === 'fulfilled') stats.value = statsRes.value
    if (entitiesRes.status === 'fulfilled') entities.value = entitiesRes.value
  } catch {
    appStore.showToast('加载注册表失败', 'error')
  } finally {
    loading.value = false
  }
}

async function handleSync() {
  syncing.value = true
  try {
    const result: RegistryIndexSyncResultDTO = await api.rebuildRegistryIndex()
    appStore.showToast(`索引同步完成，已索引 ${result.upserted_entities} 个实体`, 'success')
    await loadData()
  } catch {
    appStore.showToast('索引同步失败', 'error')
  } finally {
    syncing.value = false
  }
}

function switchTab(tab: 'all' | 'category' | 'tag' | 'article') {
  activeTab.value = tab
  currentPage.value = 1
  loadData()
}

function search() {
  currentPage.value = 1
  loadData()
}

function goPage(page: number) {
  if (page < 1 || (entities.value && !entities.value.has_next && page > currentPage.value)) return
  currentPage.value = page
  loadData()
}

onMounted(loadData)
</script>

<template>
  <div>
    <div class="main-header">
      <div class="main-header-title">注册表</div>
      <div class="main-header-actions">
        <button class="btn btn-secondary btn-sm" @click="loadData">刷新</button>
        <button class="btn btn-primary btn-sm" :disabled="syncing" @click="handleSync">
          <span v-if="syncing" class="spinner" style="width: 12px; height: 12px;"></span>
          {{ syncing ? '同步中...' : '重建索引' }}
        </button>
      </div>
    </div>

    <div class="main-content" v-if="!loading">
      <!-- 统计 -->
      <div class="stats-grid" v-if="stats">
        <div class="stat-card">
          <div class="stat-card-label">文章</div>
          <div class="stat-card-value">{{ stats.article_count }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-card-label">分类</div>
          <div class="stat-card-value">{{ stats.category_count }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-card-label">标签</div>
          <div class="stat-card-value">{{ stats.tag_count }}</div>
        </div>
      </div>

      <!-- 搜索 + 标签页 -->
      <div style="display: flex; gap: 12px; margin-bottom: 16px; align-items: center;">
        <div class="tabs" style="border: none;">
          <button class="tab" :class="{ active: activeTab === 'all' }" @click="switchTab('all')">全部</button>
          <button class="tab" :class="{ active: activeTab === 'category' }" @click="switchTab('category')">分类</button>
          <button class="tab" :class="{ active: activeTab === 'tag' }" @click="switchTab('tag')">标签</button>
          <button class="tab" :class="{ active: activeTab === 'article' }" @click="switchTab('article')">文章</button>
        </div>
        <div class="search-input" style="flex: 1; margin-left: auto;">
          <svg class="search-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.5"/>
            <path d="M11 11l3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <input class="input" v-model="searchTerm" placeholder="搜索..." @keyup.enter="search" />
        </div>
      </div>

      <!-- 实体列表 -->
      <div v-if="entities && entities.items.length > 0" class="table-container">
        <table>
          <thead>
            <tr>
              <th>标题</th>
              <th style="width: 80px;">类型</th>
              <th style="width: 80px;">状态</th>
              <th style="width: 110px;">来源</th>
              <th style="width: 160px;">同步时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in entities.items" :key="item.id">
              <td>
                <div style="font-weight: 500;">{{ item.display_name || item.title || item.entity_key }}</div>
                <div style="font-size: 12px; color: var(--text-tertiary);">{{ item.source_path || item.entity_key }}</div>
              </td>
              <td><span class="badge" :class="item.entity_type === 'article' ? 'badge-info' : item.entity_type === 'tag' ? 'badge-success' : 'badge-warning'">{{ entityTypeLabel(item.entity_type) }}</span></td>
              <td><span class="badge" :class="item.status === 'active' ? 'badge-success' : 'badge-warning'">{{ item.status }}</span></td>
              <td style="color: var(--text-tertiary);">{{ sourceKindLabel(item.source_kind) }}</td>
              <td style="color: var(--text-secondary);">{{ formatDateTime(item.synced_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else class="empty-state">
        <div class="empty-state-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
            <path d="M4 6h16M4 10h16M4 14h16M4 18h16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="empty-state-title">暂无数据</div>
        <div class="empty-state-description">尝试调整搜索条件或重建索引</div>
      </div>

      <!-- 分页 -->
      <div v-if="entities && entities.total > entities.page_size" style="display: flex; justify-content: center; gap: 8px; margin-top: 16px;">
        <button class="btn btn-secondary btn-sm" :disabled="currentPage === 1" @click="goPage(currentPage - 1)">上一页</button>
        <span style="line-height: 28px; font-size: 13px; color: var(--text-secondary);">第 {{ currentPage }} 页 / 共 {{ Math.ceil(entities.total / entities.page_size) }} 页</span>
        <button class="btn btn-secondary btn-sm" :disabled="!entities.has_next" @click="goPage(currentPage + 1)">下一页</button>
      </div>
    </div>

    <div v-else style="display: flex; align-items: center; justify-content: center; height: 300px;">
      <div class="spinner" style="width: 24px; height: 24px;"></div>
    </div>
  </div>
</template>
