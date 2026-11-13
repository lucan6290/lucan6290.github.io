<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { contentApi } from '@/api/content'
import type { ContentDirectory, DirectoryNode, DocumentSummary } from '@/types/content'
import { useAppStore } from '@/stores/app'
import { formatDate } from '@/utils/postDisplay'
import { compareContentPaths } from '@/utils/contentOrder'
import DirectoryBranch from '@/components/DirectoryBranch.vue'
import MoveContentDialog from '@/components/MoveContentDialog.vue'
import type { MoveKind, MovePlan } from '@/api/contentMoves'
import { newDraftId, relocateEditorTabs } from '@/utils/editorTabs'
import { relocateFavorites } from '@/utils/editorFavorites'
const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const documents = ref<DocumentSummary[]>([])
const directories = ref<ContentDirectory[]>([])
const directory = ref(typeof route.query.directory === 'string' ? route.query.directory : '')
const section = ref('')
const search = ref('')
const loading = ref(false)
const refreshingManually = ref(false)
const error = ref('')
const newDirectory = ref('')
const creating = ref(false)
const deleting = ref('')
const moveTarget = ref<{ source: string; kind: MoveKind } | null>(null)
let latestRequest = 0
const sections = computed(() => directories.value.filter(item => item.relative_path && !item.relative_path.includes('/')))
const directoryTree = computed(() => {
  const roots: DirectoryNode[] = []
  const byPath = new Map<string, DirectoryNode>()
  for (const item of directories.value) {
    if (!item.relative_path || (section.value && item.section !== section.value)) continue
    const node = { ...item, children: [] }
    byPath.set(item.relative_path, node)
    const parent = byPath.get(item.relative_path.slice(0, item.relative_path.lastIndexOf('/')))
    ;(parent ? parent.children : roots).push(node)
  }
  return roots
})
const visibleDocuments = computed(() => documents.value.filter(document => {
  const parent = document.relative_path.split('/').slice(0, -1).join('/')
  return (!section.value || document.section === section.value) && (!directory.value || parent === directory.value)
}))
async function refresh() {
  const request = ++latestRequest
  loading.value = true
  error.value = ''
  try {
    const index = await contentApi.list(search.value.trim())
    if (request !== latestRequest) return
    directories.value = index.directories.sort((a, b) => compareContentPaths(a.relative_path, b.relative_path))
    documents.value = index.documents.sort((a, b) => compareContentPaths(a.relative_path, b.relative_path))
    if (refreshingManually.value) appStore.showToast('刷新完成', 'success')
  }
  catch (cause) { if (request === latestRequest) error.value = cause instanceof Error ? cause.message : '读取内容失败' }
  finally {
    if (request === latestRequest) {
      loading.value = false
      refreshingManually.value = false
    }
  }
}
function refreshManually() {
  refreshingManually.value = true
  return refresh()
}
watch(search, (_value, _previous, onCleanup) => {
  latestRequest++
  loading.value = true
  const timer = setTimeout(refresh, 250)
  onCleanup(() => clearTimeout(timer))
})
function edit(document?: DocumentSummary) {
  router.push(document ? { path: '/editor', query: { id: document.relative_path } } : { path: '/editor', query: { directory: directory.value || section.value, draft: newDraftId() } })
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
async function afterMove(plan: MovePlan) {
  moveTarget.value = null
  relocateEditorTabs(plan.moves)
  relocateFavorites(plan.moves)
  const parent = plan.destination.split('/').slice(0, -1).join('/')
  directory.value = plan.kind === 'directory' ? plan.destination : parent
  section.value = ''
  await refresh()
  appStore.showToast('已移动并更新相关 Markdown 引用', 'success')
}

async function remove(document: DocumentSummary) {
  if (deleting.value || !confirm(`仅删除文档，不删除图片：\n${document.relative_path}\n确定继续？`)) return
  deleting.value = document.relative_path
  try { await contentApi.remove(document.relative_path, document.version); appStore.showToast('文档已删除', 'success'); await refresh() }
  catch (cause) { appStore.showToast(cause instanceof Error ? cause.message : '删除失败', 'error', 6000) }
  finally { deleting.value = '' }
}
onMounted(() => { refresh(); window.addEventListener('focus', refresh) })
onUnmounted(() => {
  latestRequest++
  window.removeEventListener('focus', refresh)
})
</script>
<template>
  <div>
    <div class="main-header"><div class="main-header-title">文档管理</div><div class="main-header-actions"><button class="btn btn-secondary btn-sm" :disabled="loading" @click="refreshManually">{{ refreshingManually ? '刷新中…' : '刷新' }}</button><button v-if="directory" class="btn btn-secondary btn-sm" @click="moveTarget = { source: directory, kind: 'directory' }">移动当前目录</button><button class="btn btn-primary btn-sm" @click="edit()">新建文档</button></div></div>
    <div class="main-content documents-content">
      <p v-if="error" role="alert" style="color: var(--status-error);">{{ error }}</p>
      <div class="documents-toolbar">
        <input v-model="search" class="input" aria-label="搜索文档" placeholder="搜索正文、标题、摘要、标签或路径" maxlength="200" />
        <select v-model="section" class="select" aria-label="栏目" @change="directory = ''"><option value="">全部栏目</option><option v-for="item in sections" :key="item.relative_path" :value="item.relative_path">{{ item.label }}</option></select>
        <form class="documents-directory-form" @submit.prevent="createDirectory">
          <input v-model="newDirectory" class="input" aria-label="新目录路径" placeholder="新目录相对路径，例如 knowledge/技术研习/新主题" required />
          <button class="btn btn-secondary btn-sm" :disabled="creating">新建目录</button>
        </form>
      </div>
      <p style="color: var(--text-secondary); font-size: 13px;">目录介绍 README 可单独编辑；新建文档时会使用当前选中的目录。</p>
      <div class="documents-layout">
        <nav class="card documents-tree" aria-label="文档目录">
          <button class="btn btn-ghost btn-sm" :aria-current="directory ? undefined : 'true'" @click="directory = ''">全部目录</button>
          <DirectoryBranch :nodes="directoryTree" :selected="directory" @select="directory = $event" />
        </nav>
        <div class="table-container documents-table" role="region" aria-label="文档列表" tabindex="0"><table>
        <thead><tr><th>文档</th><th>类型</th><th>标签</th><th>文件更新时间</th><th>操作</th></tr></thead>
        <tbody><tr v-for="document in visibleDocuments" :key="document.relative_path">
          <td><div style="font-weight: 500;">{{ document.title }}</div><div style="font-size: 12px; color: var(--text-secondary);">{{ document.relative_path }}</div></td>
          <td><span class="badge" :class="document.kind === 'introduction' ? 'badge-info' : 'badge-success'">{{ document.kind === 'introduction' ? '目录介绍' : '文档' }}</span></td><td>{{ document.tags.join('、') || '—' }}</td><td>{{ formatDate(document.modified_at) }}</td>
          <td><div style="display: flex; gap: 4px;"><button class="btn btn-ghost btn-sm" @click="edit(document)">编辑</button><button class="btn btn-ghost btn-sm" @click="moveTarget = { source: document.relative_path, kind: 'document' }">移动</button><button class="btn btn-ghost btn-sm" :disabled="!!deleting" @click="remove(document)">删除</button></div></td>
        </tr><tr v-if="!visibleDocuments.length"><td colspan="5">{{ loading ? '读取中…' : search.trim() ? '没有匹配的文档。' : '此处还没有文档。' }}</td></tr></tbody>
      </table></div>
      </div>
    </div>
    <MoveContentDialog v-if="moveTarget" :source="moveTarget.source" :kind="moveTarget.kind" @close="moveTarget = null" @moved="afterMove" />
  </div>
</template>

<style scoped>
.documents-content { display: flex; flex-direction: column; overflow: hidden; }
.documents-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) clamp(110px, 16%, 160px) minmax(0, 1.2fr);
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.documents-directory-form { display: flex; align-items: center; gap: 8px; min-width: 0; }
.documents-directory-form .input { min-width: 0; }
.documents-directory-form .btn { flex-shrink: 0; }
.documents-layout {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(150px, 220px) minmax(0, 1fr);
  grid-template-rows: minmax(0, 1fr);
  gap: 16px;
  align-items: stretch;
}
.documents-tree { padding: 8px; max-height: 100%; overflow: auto; }
.documents-tree > [aria-current='true'] { font-weight: 700; }
.documents-table { max-height: 100%; overflow: auto; overscroll-behavior-y: contain; }
</style>
