<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { contentApi } from '@/api/content'
import type { ContentIndex } from '@/types/content'
import { formatDate } from '@/utils/postDisplay'
const router = useRouter()
const index = ref<ContentIndex>({ directories: [], documents: [] })
const error = ref('')
const loading = ref(false)
const articles = computed(() => index.value.documents.filter(item => item.kind === 'article'))
const sections = computed(() => index.value.directories.filter(item => item.relative_path && !item.relative_path.includes('/')))
const recent = computed(() => [...index.value.documents].sort((a, b) => b.modified_at.localeCompare(a.modified_at)).slice(0, 8))
async function refresh() {
  if (loading.value) return
  loading.value = true
  try { index.value = await contentApi.list(); error.value = '' }
  catch (cause) { error.value = cause instanceof Error ? cause.message : '读取失败' }
  finally { loading.value = false }
}
onMounted(() => { refresh(); window.addEventListener('focus', refresh) })
onUnmounted(() => window.removeEventListener('focus', refresh))
</script>
<template>
  <div>
    <div class="main-header"><div class="main-header-title">内容库</div><button class="btn btn-secondary btn-sm" :disabled="loading" @click="refresh">刷新</button></div>
    <div class="main-content">
      <p v-if="error" role="alert" style="color: var(--status-error);">{{ error }}</p>
      <div class="stats-grid">
        <div class="stat-card"><div class="stat-card-label">文章总数</div><div class="stat-card-value">{{ articles.length }}</div></div>
        <div class="stat-card"><div class="stat-card-label">目录介绍</div><div class="stat-card-value">{{ index.documents.length - articles.length }}</div></div>
        <div v-for="section in sections" :key="section.relative_path" class="stat-card"><div class="stat-card-label">{{ section.label }}</div><div class="stat-card-value">{{ articles.filter(item => item.section === section.section).length }}</div></div>
      </div>
      <div class="card" style="margin-top: 20px;"><h3>最近修改</h3><p style="color: var(--text-secondary);">包括桌面端、外部编辑器与 AI 保存的内容。</p>
        <div v-for="document in recent" :key="document.relative_path" class="list-item" style="justify-content: space-between;"><div><button class="btn btn-ghost" @click="router.push({ path: '/editor', query: { id: document.relative_path } })">{{ document.title }}</button><div style="font-size: 12px; color: var(--text-secondary);">{{ document.relative_path }}</div></div><span>{{ formatDate(document.modified_at) }}</span></div>
      </div>
    </div>
  </div>
</template>
