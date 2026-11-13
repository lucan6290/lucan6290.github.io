<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
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
const search = ref('')
const searchOpen = ref(false)
const searchButton = ref<HTMLButtonElement | null>(null)
const searchInput = ref<HTMLInputElement | null>(null)
const loading = ref(false)
const refreshingManually = ref(false)
const error = ref('')
const newDirectory = ref('')
const directoryDialog = ref<HTMLDialogElement | null>(null)
const directoryError = ref('')
const creating = ref(false)
const deleting = ref('')
const moveTarget = ref<{ source: string; kind: MoveKind } | null>(null)
let latestRequest = 0
const directoryTree = computed(() => {
  const roots: DirectoryNode[] = []
  const byPath = new Map<string, DirectoryNode>()
  for (const item of directories.value) {
    if (!item.relative_path) continue
    const node = { ...item, children: [] }
    byPath.set(item.relative_path, node)
    const parent = byPath.get(item.relative_path.slice(0, item.relative_path.lastIndexOf('/')))
    ;(parent ? parent.children : roots).push(node)
  }
  return roots
})
const visibleDocuments = computed(() => documents.value.filter(document => {
  if (!directory.value) return true
  if (!directory.value.includes('/')) return document.relative_path.startsWith(`${directory.value}/`)
  const parent = document.relative_path.split('/').slice(0, -1).join('/')
  return parent === directory.value
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
async function toggleSearch() {
  searchOpen.value = !searchOpen.value
  if (searchOpen.value) {
    await nextTick()
    searchInput.value?.focus()
  } else {
    search.value = ''
    searchButton.value?.focus()
  }
}
function edit(document?: DocumentSummary) {
  router.push(document ? { path: '/editor', query: { id: document.relative_path } } : { path: '/editor', query: { directory: directory.value, draft: newDraftId() } })
}
function openDirectoryDialog() {
  newDirectory.value = ''
  directoryError.value = ''
  directoryDialog.value?.showModal()
}
async function createDirectory() {
  if (!newDirectory.value.trim() || creating.value) return
  creating.value = true
  directoryError.value = ''
  try {
    const created = await contentApi.createDirectory(newDirectory.value.trim())
    directory.value = created.relative_path
    directoryDialog.value?.close()
    await refresh()
    appStore.showToast('目录已创建', 'success')
  } catch (cause) { directoryError.value = cause instanceof Error ? cause.message : '创建目录失败' }
  finally { creating.value = false }
}
async function afterMove(plan: MovePlan) {
  moveTarget.value = null
  relocateEditorTabs(plan.moves)
  relocateFavorites(plan.moves)
  const parent = plan.destination.split('/').slice(0, -1).join('/')
  directory.value = plan.kind === 'directory' ? plan.destination : parent
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
    <div class="main-header documents-header">
      <div class="main-header-title">文档管理</div>
      <div class="main-header-actions">
        <div class="documents-search-group" @keydown.esc="searchOpen && toggleSearch()">
          <button ref="searchButton" class="btn btn-ghost btn-sm documents-search-button" type="button" aria-label="搜索文档"
            :title="searchOpen ? '收起搜索' : '搜索文档'" :aria-expanded="searchOpen" aria-controls="documents-search" @click="toggleSearch">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.5" />
              <path d="M11 11l3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
            </svg>
          </button>
          <input v-show="searchOpen" id="documents-search" ref="searchInput" v-model="search" class="input documents-search" type="search"
            aria-label="搜索文档" placeholder="搜索正文、标题、摘要、标签或路径" maxlength="200" />
        </div>
        <button class="btn btn-secondary btn-sm" type="button" :disabled="loading" @click="refreshManually">{{ refreshingManually ? '刷新中…' : '刷新' }}</button>
        <button v-if="directory" class="btn btn-secondary btn-sm" type="button" @click="moveTarget = { source: directory, kind: 'directory' }">移动当前目录</button>
        <button class="btn btn-secondary btn-sm" type="button" aria-haspopup="dialog" :disabled="creating" @click="openDirectoryDialog">新建目录</button>
        <button class="btn btn-primary btn-sm" type="button" @click="edit()">新建文档</button>
      </div>
    </div>
    <div class="main-content documents-content">
      <p v-if="error" role="alert" style="color: var(--status-error);">{{ error }}</p>
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
    <dialog ref="directoryDialog" class="documents-directory-dialog" aria-labelledby="new-directory-title" @cancel="creating && $event.preventDefault()">
      <h2 id="new-directory-title">新建目录</h2>
      <form @submit.prevent="createDirectory">
        <label for="new-directory-path">内容库相对路径</label>
        <input id="new-directory-path" v-model="newDirectory" class="input" placeholder="例如 knowledge/技术研习/新主题"
          autofocus required :disabled="creating" />
        <p v-if="directoryError" class="documents-directory-error" role="alert">{{ directoryError }}</p>
        <div class="documents-directory-actions">
          <button class="btn btn-secondary btn-sm" type="button" :disabled="creating" @click="directoryDialog?.close()">取消</button>
          <button class="btn btn-primary btn-sm" type="submit" :disabled="creating || !newDirectory.trim()">{{ creating ? '创建中…' : '创建目录' }}</button>
        </div>
      </form>
    </dialog>
    <MoveContentDialog v-if="moveTarget" :source="moveTarget.source" :kind="moveTarget.kind" @close="moveTarget = null" @moved="afterMove" />
  </div>
</template>

<style scoped>
.documents-content { display: flex; flex-direction: column; overflow: hidden; }
.documents-header { gap: 12px; flex-wrap: wrap; }
.documents-search-group { display: flex; align-items: center; gap: 8px; max-width: 100%; }
.documents-search-button { flex-shrink: 0; padding-inline: 7px; }
.documents-search-button[aria-expanded='true'] { background: var(--bg-element-hover); }
.documents-search { width: min(300px, 40vw); min-width: 0; }
.documents-header .main-header-actions { flex-wrap: wrap; margin-inline-start: auto; }
.documents-directory-dialog {
  width: min(420px, calc(100vw - 32px));
  margin: auto;
  padding: 20px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-panel);
  color: var(--text-primary);
}
.documents-directory-dialog::backdrop { background: rgb(0 0 0 / .38); }
.documents-directory-dialog h2 { margin-bottom: 12px; font-size: 16px; }
.documents-directory-dialog label { display: block; margin-bottom: 6px; }
.documents-directory-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
.documents-directory-error { color: var(--status-error); overflow-wrap: anywhere; }
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
