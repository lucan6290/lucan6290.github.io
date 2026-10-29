<script setup lang="ts">
import { computed, reactive, ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave, onBeforeRouteUpdate } from 'vue-router'
import { isTauri } from '@tauri-apps/api/core'
import { getCurrentWindow } from '@tauri-apps/api/window'
import { contentApi, ContentApiError } from '@/api/content'
import { useAppStore } from '@/stores/app'
import { DocumentSession } from '@/utils/documentSession'
import { compareContentPaths } from '@/utils/contentOrder'
import { createArticleTemplate, fillArticleTitle, isArticleDocument } from '@/utils/articleTemplate'
import type { ContentDirectory } from '@/types/content'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const session = reactive(new DocumentSession())
const loading = ref(false)
const directories = ref<ContentDirectory[]>([])
const directory = ref('')
const filename = ref('')
const purpose = ref('article')
const articleDocument = computed(() => isArticleDocument(filename.value, purpose.value === 'article'))
const draftNotice = ref('')
let draftStartedAt = new Date()
const error = ref('')
const checkError = ref('')
const saveAsVisible = ref(false)
const saveAsDirectory = ref('')
const saveAsName = ref('')
const leaveVisible = ref(false)
const editor = ref<HTMLTextAreaElement | null>(null)
let resolveLeave: ((allow: boolean) => void) | null = null
let pendingLeave: Promise<boolean> | null = null
let interval: ReturnType<typeof setInterval> | undefined
let unlistenClose: (() => void) | undefined
let disposed = false
let closing = false

function message(cause: unknown) {
  if (cause instanceof ContentApiError) {
    const details = cause.details ? `：${typeof cause.details === 'string' ? cause.details : JSON.stringify(cause.details)}` : ''
    return `${cause.message}${details} (${cause.status})`
  }
  return cause instanceof Error ? cause.message : '请求失败，请检查后端连接'
}

async function loadDirectories() {
  try { directories.value = (await contentApi.list()).directories.sort((a, b) => compareContentPaths(a.relative_path, b.relative_path)) }
  catch (cause) { checkError.value = message(cause) }
}

async function openDocument() {
  const path = typeof route.query.id === 'string' ? route.query.id : null
  // 新建/另存成功后更新地址；保留请求期间继续输入的文本。
  if (path && path === session.path && session.baseline) return
  draftStartedAt = new Date()
  session.begin(path, path ? '' : createArticleTemplate(draftStartedAt))
  directory.value = typeof route.query.directory === 'string' ? route.query.directory : ''
  filename.value = ''
  purpose.value = path ? 'auto' : 'article'
  draftNotice.value = ''
  error.value = ''
  checkError.value = ''
  const generation = session.generation
  loading.value = !!path
  if (!path) return
  try { session.load(await contentApi.read(path), generation) }
  catch (cause) { if (generation === session.generation) error.value = message(cause) }
  finally { if (generation === session.generation) loading.value = false }
}

function newPath(parent: string, name: string) {
  if (!name || name.includes('/') || name.includes('\\') || !/\.md$/i.test(name)) {
    throw new Error('请输入实际文件名，必须以 .md 结尾且不能包含目录分隔符')
  }
  return parent ? `${parent}/${name}` : name
}

function fillEmptyTitle() {
  if (!session.path && articleDocument.value) session.text = fillArticleTitle(session.text, filename.value)
}

watch(articleDocument, article => {
  if (session.path) return
  const replaced = session.replaceDraft(article ? createArticleTemplate(draftStartedAt) : '')
  draftNotice.value = replaced ? '' : '已保留全部已编辑内容。普通文章请填写完整六字段；说明文档可保留当前头部。'
})

async function updateAddress() {
  if (session.path && route.query.id !== session.path) {
    await router.replace({ path: '/editor', query: { id: session.path } })
  }
}

async function handleSave(): Promise<boolean> {
  if (loading.value || session.saving || (session.path && !session.baseline)) return false
  error.value = ''
  const generation = session.generation
  try {
    const target = session.path ? undefined : newPath(directory.value, filename.value)
    const creating = !session.path
    const article = creating ? articleDocument.value : purpose.value === 'auto' ? undefined : purpose.value === 'article'
    fillEmptyTitle()
    const changed = session.dirty || !session.baseline
    await session.save(contentApi, target, article)
    if (generation !== session.generation) return false
    if (creating) purpose.value = article ? 'article' : 'document'
    if (!leaveVisible.value) await updateAddress()
    appStore.showToast(changed ? '文档已保存' : '内容未变化，无需写入', 'success')
    return !session.dirty
  } catch (cause) {
    if (generation !== session.generation) return false
    error.value = message(cause)
    if (cause instanceof ContentApiError && (cause.status === 409 || cause.status === 404)) await checkExternal()
    return false
  }
}

async function checkExternal() {
  if (document.hidden || loading.value) return
  const generation = session.generation
  const previousVersion = session.baseline?.version
  const scrollTop = editor.value?.scrollTop
  const selectionStart = editor.value?.selectionStart
  const selectionEnd = editor.value?.selectionEnd
  const selectionDirection = editor.value?.selectionDirection
  try {
    await session.check(contentApi)
    await nextTick()
    if (generation !== session.generation) return
    checkError.value = ''
    if (editor.value && scrollTop !== undefined && previousVersion !== session.baseline?.version && session.externalUpdated && !session.dirty) {
      if (selectionStart !== undefined && selectionEnd !== undefined) editor.value.setSelectionRange(selectionStart, selectionEnd, selectionDirection)
      editor.value.scrollTop = scrollTop
    }
  } catch (cause) {
    if (generation === session.generation) checkError.value = `外部检查暂未成功，已保留当前文本：${message(cause)}`
  }
}

async function reloadFromDisk() {
  if (!session.path || session.saving || loading.value) return
  if (session.dirty && !window.confirm('放弃本地未保存修改，并重新读取磁盘文件？')) return
  const path = session.path
  const generation = ++session.generation
  loading.value = true
  error.value = ''
  try {
    session.load(await contentApi.read(path), generation)
    checkError.value = ''
    session.externalUpdated = false
  } catch (cause) { if (generation === session.generation) error.value = message(cause) }
  finally { if (generation === session.generation) loading.value = false }
}

async function copyLocal() {
  try {
    await navigator.clipboard.writeText(session.rawContent())
    appStore.showToast('本地修改已复制', 'success')
  } catch { appStore.showToast('复制失败，请在源码中全选复制', 'error') }
}

function openSaveAs() {
  const parts = (session.path || '').split('/')
  saveAsName.value = parts.pop() || filename.value
  saveAsDirectory.value = session.path ? parts.join('/') : directory.value
  saveAsVisible.value = true
}

async function saveAs() {
  const generation = session.generation
  error.value = ''
  try {
    await session.saveAs(contentApi, newPath(saveAsDirectory.value, saveAsName.value))
    if (generation !== session.generation) return
    saveAsVisible.value = false
    await updateAddress()
    appStore.showToast('已另存为新文件', 'success')
  } catch (cause) { if (generation === session.generation) error.value = message(cause) }
}

function confirmLeave(): Promise<boolean> {
  if (pendingLeave) return pendingLeave
  if (session.saving) {
    appStore.showToast('保存正在进行，请完成后再离开', 'warning')
    return Promise.resolve(false)
  }
  if (!session.dirty) return Promise.resolve(true)
  leaveVisible.value = true
  pendingLeave = new Promise(resolve => { resolveLeave = resolve })
  return pendingLeave
}

async function chooseLeave(action: 'save' | 'discard' | 'cancel') {
  if (session.saving) return
  if (action === 'save' && !(await handleSave())) return
  leaveVisible.value = false
  resolveLeave?.(action !== 'cancel')
  resolveLeave = null
  pendingLeave = null
}

onBeforeRouteLeave(() => confirmLeave())
onBeforeRouteUpdate(to => {
  // 仅已成功创建文件的地址同步可跳过询问与重新读取。
  if (to.query.id === session.path && session.baseline) return true
  return confirmLeave()
})

function beforeUnload(event: BeforeUnloadEvent) {
  if (session.dirty || session.saving) { event.preventDefault(); event.returnValue = '' }
}

function onFocus() { void loadDirectories(); void checkExternal() }

watch(() => [route.query.id, route.query.directory], () => { void openDocument() }, { immediate: true })
onMounted(async () => {
  void loadDirectories()
  interval = setInterval(() => { void checkExternal() }, 2000)
  window.addEventListener('focus', onFocus)
  window.addEventListener('beforeunload', beforeUnload)
  if (isTauri()) {
    try {
      const unlisten = await getCurrentWindow().onCloseRequested(async event => {
        if (!session.dirty && !session.saving) return
        event.preventDefault()
        if (closing) return
        closing = true
        try { if (await confirmLeave()) await getCurrentWindow().destroy() }
        catch (cause) { error.value = `关闭窗口失败：${message(cause)}` }
        finally { closing = false }
      })
      if (disposed) unlisten()
      else unlistenClose = unlisten
    } catch (cause) { error.value = `窗口关闭保护注册失败：${message(cause)}` }
  }
})
onBeforeUnmount(() => {
  disposed = true
  clearInterval(interval)
  unlistenClose?.()
  window.removeEventListener('focus', onFocus)
  window.removeEventListener('beforeunload', beforeUnload)
  resolveLeave?.(false)
})
</script>

<template>
  <div>
    <div class="main-header">
      <div class="main-header-title">{{ session.path ? '编辑文档' : '新建文档' }}{{ session.dirty ? ' · 未保存' : '' }}</div>
      <div class="main-header-actions">
        <button class="btn btn-secondary btn-sm" @click="router.back()">返回</button>
        <button class="btn btn-secondary btn-sm" :disabled="session.saving || loading || (!!session.path && !session.baseline)" @click="openSaveAs">另存为</button>
        <button class="btn btn-primary btn-sm" :disabled="session.saving || loading || (!!session.path && !session.baseline)" @click="handleSave">{{ session.saving ? '保存中...' : '保存' }}</button>
      </div>
    </div>
    <div class="main-content">
      <p v-if="error" role="alert" class="card" style="color: var(--danger, #dc2626); white-space: pre-wrap;">{{ error }}</p>
      <p v-if="checkError" role="status" class="card">{{ checkError }}</p>
      <div v-if="!session.path" class="card" style="margin-bottom: 16px; display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
        <label>现有目录
          <select v-model="directory" class="select" :disabled="session.saving">
            <option v-if="!directories.some(item => item.relative_path === '')" value="">内容根目录</option>
            <option v-for="item in directories" :key="item.relative_path" :value="item.relative_path">{{ item.relative_path || '内容根目录' }}</option>
          </select>
        </label>
        <label>实际文件名<input v-model="filename" class="input" placeholder="例如：01-中文 笔记.md" :disabled="session.saving" @change="fillEmptyTitle" /></label>
        <label>文档用途
          <select v-model="purpose" class="select" :disabled="session.saving">
            <option value="article">普通文章</option>
            <option value="document">说明文档</option>
          </select>
        </label>
        <p style="grid-column: 1 / -1; color: var(--text-secondary); margin: 0;">{{ articleDocument ? '请填写标题与摘要，正文一级标题应与 title 一致；日期已记录开始写作时间。' : '说明文档可直接写正文；README.md 与 AGENTS.md 自动免用文章模板。' }}</p>
        <p v-if="draftNotice" role="status" style="grid-column: 1 / -1; margin: 0;">{{ draftNotice }}</p>
      </div>
      <div v-else-if="session.baseline" class="card" style="margin-bottom: 16px;">
        <label>本次编辑用途
          <select v-model="purpose" class="select" :disabled="session.saving">
            <option value="auto">自动识别</option>
            <option value="article">普通文章</option>
            <option value="document">说明文档</option>
          </select>
        </label>
        <p style="color: var(--text-secondary); margin-bottom: 0;">选择仅用于本次编辑，重新打开后恢复自动识别；说明文档按原文保存。</p>
      </div>
      <div v-if="session.missing || session.external" class="card" role="alert" style="margin-bottom: 16px;">
        <p>{{ session.missing ? '原文件已被删除或移动。本地文本已保留，保存不会自动重建原路径。' : '磁盘文件已变化。本地文本与原读取版本已保留，保存时仍会检查冲突。' }}</p>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          <button class="btn btn-secondary btn-sm" @click="copyLocal">复制本地修改</button>
          <button class="btn btn-secondary btn-sm" :disabled="session.saving || loading" @click="reloadFromDisk">放弃本地修改并重载</button>
          <button class="btn btn-secondary btn-sm" :disabled="session.saving" @click="openSaveAs">另存为新文件</button>
        </div>
        <details v-if="session.external" style="margin-top: 12px;" open>
          <summary>本地与最新磁盘文本对照</summary>
          <div class="editor-comparison">
            <div><strong>本地未保存文本</strong><pre>{{ session.text }}</pre></div>
            <div><strong>最新磁盘文本</strong><pre>{{ session.external.raw_content.replace(/^\uFEFF/, '') }}</pre></div>
          </div>
        </details>
      </div>
      <p v-else-if="session.externalUpdated" role="status">已读取外部更新。</p>
      <div class="card" style="padding: 0; overflow: hidden;">
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 8px 12px; border-bottom: 1px solid var(--border-subtle);">
          <span style="font-size: 12px; color: var(--text-secondary);">{{ loading ? '读取中...' : 'Markdown 源码编辑' }}</span>
          <span style="font-size: 12px; color: var(--text-tertiary); overflow-wrap: anywhere;">{{ session.path || '尚未创建' }}</span>
          <button v-if="session.path" class="btn btn-secondary btn-sm" :disabled="session.saving || loading" @click="checkExternal">检查外部变化</button>
          <button v-if="session.path && !session.baseline" class="btn btn-secondary btn-sm" @click="reloadFromDisk">重试读取</button>
        </div>
        <textarea ref="editor" v-model="session.text" class="editor-content" :disabled="loading || (!!session.path && !session.baseline)" aria-label="完整 Markdown 源码" spellcheck="false" />
      </div>
    </div>
    <div v-if="leaveVisible" class="editor-modal-backdrop">
      <section role="dialog" aria-modal="true" aria-labelledby="leave-title" class="card editor-dialog">
        <h3 id="leave-title">有未保存修改</h3><p>保存成功后离开，或明确放弃本地修改。</p>
        <p v-if="error" role="alert">{{ error }}</p>
        <div class="editor-dialog-actions">
          <button class="btn btn-secondary" :disabled="session.saving" @click="chooseLeave('cancel')">取消</button>
          <button class="btn btn-secondary" :disabled="session.saving" @click="chooseLeave('discard')">放弃并离开</button>
          <button class="btn btn-primary" :disabled="session.saving" @click="chooseLeave('save')">{{ session.saving ? '保存中...' : '保存并离开' }}</button>
        </div>
      </section>
    </div>
    <div v-if="saveAsVisible" class="editor-modal-backdrop">
      <form role="dialog" aria-modal="true" aria-labelledby="save-as-title" class="card editor-dialog" @submit.prevent="saveAs">
        <h3 id="save-as-title">另存为新文件</h3><p>目标必须不存在；新文件使用 UTF-8 无 BOM 与 LF 换行。</p>
        <label>现有目录<select v-model="saveAsDirectory" class="select" :disabled="session.saving"><option value="">内容根目录</option><option v-for="item in directories.filter(item => item.relative_path)" :key="item.relative_path" :value="item.relative_path">{{ item.relative_path }}</option></select></label>
        <label>实际文件名<input v-model="saveAsName" class="input" placeholder="新文档.md" :disabled="session.saving" /></label>
        <p v-if="error" role="alert">{{ error }}</p>
        <div class="editor-dialog-actions"><button class="btn btn-secondary" type="button" :disabled="session.saving" @click="saveAsVisible = false">取消</button><button class="btn btn-primary" type="submit" :disabled="session.saving">{{ session.saving ? '创建中...' : '创建新文件' }}</button></div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.editor-content { width: 100%; min-height: 500px; padding: 16px; font-family: var(--font-mono); font-size: 13px; line-height: 1.7; border: none; outline: none; resize: vertical; background: var(--bg-panel); color: var(--text-primary); }
.editor-modal-backdrop { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 24px; background: rgba(0, 0, 0, 0.4); }
.editor-dialog { width: min(560px, 100%); max-height: 90vh; overflow: auto; background: var(--bg-panel); }
.editor-dialog label { display: block; margin: 12px 0; }
.editor-dialog-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 20px; }
.editor-comparison { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 16px; margin-top: 12px; }
.editor-comparison pre { max-height: 320px; overflow: auto; white-space: pre-wrap; overflow-wrap: anywhere; font-family: var(--font-mono); }
@media (max-width: 720px) { .editor-comparison { grid-template-columns: 1fr; } }
</style>
