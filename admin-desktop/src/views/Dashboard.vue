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
      <section class="card recent-card" aria-labelledby="recent-heading">
        <h3 id="recent-heading">最近修改</h3>
        <p>包括桌面端、外部编辑器与 AI 保存的内容。</p>
        <ul v-if="recent.length" class="recent-list">
          <li v-for="document in recent" :key="document.relative_path" class="recent-item">
            <div>
              <button
                type="button"
                class="recent-title"
                :title="document.title"
                @click="router.push({ path: '/editor', query: { id: document.relative_path } })"
              >{{ document.title }}</button>
              <div class="recent-path" :title="document.relative_path">{{ document.relative_path }}</div>
            </div>
            <time class="recent-date" :datetime="document.modified_at">{{ formatDate(document.modified_at) }}</time>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>

<style scoped>
.stats-grid {
  grid-template-columns: none;
  grid-auto-flow: column;
  grid-auto-columns: minmax(120px, 1fr);
  overflow-x: auto;
}

.stat-card {
  padding-inline: 16px;
}

.stat-card-label {
  overflow-wrap: anywhere;
}

.recent-card p {
  margin-top: 4px;
  color: var(--text-secondary);
}

.recent-list {
  margin: 12px 0 0;
  padding: 0;
  list-style: none;
}

.recent-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 16px;
  padding: 10px 0;
  border-top: 1px solid var(--border-subtle);
}

.recent-title,
.recent-path {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-title {
  display: block;
  max-width: 100%;
  padding: 0;
  border: 0;
  background: none;
  color: var(--text-primary);
  font: inherit;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
}

.recent-title:hover {
  color: var(--accent-primary);
  text-decoration: underline;
}

.recent-title:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 2px;
}

.recent-path,
.recent-date {
  color: var(--text-secondary);
  font-size: 12px;
}

.recent-date {
  text-align: right;
  white-space: nowrap;
}
</style>
