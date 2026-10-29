<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { contentApi } from '@/api/content'
import type { ContentDirectory, DocumentSummary } from '@/types/content'
import { useAppStore } from '@/stores/app'
import { formatDate } from '@/utils/postDisplay'
import { compareContentPaths } from '@/utils/contentOrder'
const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const documents = ref<DocumentSummary[]>([])
const directories = ref<ContentDirectory[]>([])
const directory = ref(typeof route.query.directory === 'string' ? route.query.directory : '')
const section = ref('')
const search = ref('')
const loading = ref(false)
const error = ref('')
const newDirectory = ref('')
const creating = ref(false)
const deleting = ref('')
const sections = computed(() => directories.value.filter(item => item.relative_path && !item.relative_path.includes('/')))
const visibleDocuments = computed(() => documents.value.filter(document => {
  const parent = document.relative_path.split('/').slice(0, -1).join('/')
  const query = search.value.trim().toLowerCase()
  return (!section.value || document.section === section.value) && (!directory.value || parent === directory.value)
    && (!query || [document.title, document.relative_path, ...document.tags].some(value => value.toLowerCase().includes(query)))
}))
async function refresh() {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    const index = await contentApi.list()
    directories.value = index.directories.sort((a, b) => compareContentPaths(a.relative_path, b.relative_path))
    documents.value = index.documents.sort((a, b) => compareContentPaths(a.relative_path, b.relative_path))
  }
  catch (cause) { error.value = cause instanceof Error ? cause.message : '读取内容失败' }
  finally { loading.value = false }
}
function edit(document?: DocumentSummary) {
  router.push(document ? { path: '/editor', query: { id: document.relative_path } } : { path: '/editor', query: { directory: directory.value || section.value } })
}
async function createDirectory() {
  if (!newDirectory.value.trim() || creating.value) return
  creating.value = true
  try {
    const created = await contentApi.createDirectory(newDirectory.value.trim())
    directory.value = created.relative_path
    newDirectory.value = ''
    await refresh()
    appStore.showToast('目录已创建', 'success')
  } catch (cause) { appStore.showToast(cause instanceof Error ? cause.message : '创建目录失败', 'error') }
  finally { creating.value = false }
}
async function remove(document: DocumentSummary) {
  if (deleting.value || !confirm(`仅删除文档，不删除图片：\n${document.relative_path}\n确定继续？`)) return
  deleting.value = document.relative_path
  try { await contentApi.remove(document.relative_path, document.version); appStore.showToast('文档已删除', 'success'); await refresh() }
  catch (cause) { appStore.showToast(cause instanceof Error ? cause.message : '删除失败', 'error', 6000) }
  finally { deleting.value = '' }
}
onMounted(() => { refresh(); window.addEventListener('focus', refresh) })
onUnmounted(() => window.removeEventListener('focus', refresh))
</script>
<template>
  <div>
    <div class="main-header"><div class="main-header-title">文档管理</div><div class="main-header-actions"><button class="btn btn-secondary btn-sm" :disabled="loading" @click="refresh">刷新</button><button class="btn btn-primary btn-sm" @click="edit()">新建文档</button></div></div>
    <div class="main-content">
      <p v-if="error" role="alert" style="color: var(--status-error);">{{ error }}</p>
      <div style="display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;">
        <input v-model="search" class="input" aria-label="搜索文档" placeholder="搜索标题、路径或标签" style="flex: 1; min-width: 180px;" />
        <select v-model="section" class="select" aria-label="栏目" @change="directory = ''"><option value="">全部栏目</option><option v-for="item in sections" :key="item.relative_path" :value="item.relative_path">{{ item.label }}</option></select>
        <select v-model="directory" class="select" aria-label="目录"><option value="">全部目录</option><option v-for="item in directories.filter(d => d.relative_path && (!section || d.section === section))" :key="item.relative_path" :value="item.relative_path">{{ item.relative_path }}</option></select>
      </div>
      <form style="display: flex; gap: 8px; margin-bottom: 16px;" @submit.prevent="createDirectory"><input v-model="newDirectory" class="input" aria-label="新目录路径" placeholder="新目录相对路径，例如 knowledge/技术研习/新主题" required /><button class="btn btn-secondary btn-sm" :disabled="creating">新建目录</button></form>
      <p style="color: var(--text-secondary); font-size: 13px;">目录介绍 README 可单独编辑；新建文档时会使用当前选中的目录。</p>
      <div class="table-container"><table>
        <thead><tr><th>文档</th><th>类型</th><th>标签</th><th>文件更新时间</th><th>操作</th></tr></thead>
        <tbody><tr v-for="document in visibleDocuments" :key="document.relative_path">
          <td><div style="font-weight: 500;">{{ document.title }}</div><div style="font-size: 12px; color: var(--text-secondary);">{{ document.relative_path }}</div></td>
          <td><span class="badge" :class="document.kind === 'introduction' ? 'badge-info' : 'badge-success'">{{ document.kind === 'introduction' ? '目录介绍' : '文档' }}</span></td><td>{{ document.tags.join('、') || '—' }}</td><td>{{ formatDate(document.modified_at) }}</td>
          <td><div style="display: flex; gap: 4px;"><button class="btn btn-ghost btn-sm" @click="edit(document)">编辑</button><button class="btn btn-ghost btn-sm" :disabled="!!deleting" @click="remove(document)">删除</button></div></td>
        </tr><tr v-if="!visibleDocuments.length"><td colspan="5">{{ loading ? '读取中…' : '此处还没有文档。' }}</td></tr></tbody>
      </table></div>
    </div>
  </div>
</template>
