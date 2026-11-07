<script setup lang="ts">
import { computed, shallowRef, ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave, onBeforeRouteUpdate } from 'vue-router'
import { isTauri } from '@tauri-apps/api/core'
import { getCurrentWindow } from '@tauri-apps/api/window'
import { contentApi, ContentApiError } from '@/api/content'
import { mediaApi } from '@/api/media'
import { fileBase64, imageExtensions, insertImageReferences } from '@/utils/mediaImport'
import { useAppStore } from '@/stores/app'
import { activateEditorTab, editorTabLabel, editorTabQuery, editorTabs, newDraftId, removeEditorTab, type EditorTab } from '@/utils/editorTabs'
import { compareContentPaths } from '@/utils/contentOrder'
import { createArticleTemplate, fillArticleTitle, isArticleDocument } from '@/utils/articleTemplate'
import type { ContentDirectory } from '@/types/content'
import MarkdownPreview from '@/components/MarkdownPreview.vue'
import DocumentBacklinks from '@/components/DocumentBacklinks.vue'
import ArticleForm from '@/components/ArticleForm.vue'
import EditorQuickSwitch from '@/components/EditorQuickSwitch.vue'
import { applyMarkdownCommand, markdownCommands, type MarkdownCommand } from '@/utils/editorCommands'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
function tabFromRoute() {
  return activateEditorTab(
    typeof route.query.id === 'string' ? route.query.id : null,
    typeof route.query.draft === 'string' ? route.query.draft : undefined,
    typeof route.query.directory === 'string' ? route.query.directory : '',
  )
}
const activeTab = shallowRef(tabFromRoute())
const session = computed(() => activeTab.value.session)
const loading = ref(false)
const directories = ref<ContentDirectory[]>([])
const directory = computed({ get: () => activeTab.value.directory, set: value => { activeTab.value.directory = value } })
const filename = computed({ get: () => activeTab.value.filename, set: value => { activeTab.value.filename = value } })
const purpose = computed({ get: () => activeTab.value.purpose, set: value => { activeTab.value.purpose = value } })
const articleDocument = computed(() => isArticleDocument(filename.value, purpose.value === 'article'))
const draftNotice = computed(() => activeTab.value.draftNotice)
const error = ref('')
const checkError = ref('')
const saveAsVisible = ref(false)
const saveAsDirectory = ref('')
const saveAsName = ref('')
const leaveVisible = ref(false)
const leaveTargets = shallowRef<EditorTab[]>([])
const editor = ref<HTMLTextAreaElement | null>(null)
const quickSwitch = ref<InstanceType<typeof EditorQuickSwitch> | null>(null)
const imagePicker = ref<HTMLInputElement | null>(null)
const importingImages = ref(false)
const showPreview = ref(true)
const readingMode = ref(false)
const previewDirectory = computed(() => session.value.path?.split('/').slice(0, -1).join('/') ?? directory.value)
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

async function applyCommand(command: MarkdownCommand) {
  const current = session.value
  const input = editor.value
  if (!input || input.disabled || readingMode.value) return
  const generation = current.generation
  const result = applyMarkdownCommand(current.text, input.selectionStart, input.selectionEnd, command)
  current.text = result.text
  await nextTick()
  if ((current !== session.value || generation !== current.generation)) return
  editor.value?.focus()
  editor.value?.setSelectionRange(result.start, result.end)
}

function editorShortcut(event: KeyboardEvent) {
  if (event.isComposing) return
  const key = event.key.toLowerCase()
  if ((event.ctrlKey || event.metaKey) && !event.altKey) {
    if (key === 'p') {
      event.preventDefault()
      if (!leaveVisible.value) void quickSwitch.value?.open()
    } else if (key === 's') {
      event.preventDefault()
      if (!leaveVisible.value && !saveAsVisible.value) void handleSave()
    } else if (event.target === editor.value) {
      const command = key === 'b' ? 'bold' : key === 'i' ? 'italic' : key === 'k' ? 'link' : null
      if (command) {
        event.preventDefault()
        void applyCommand(command)
      }
    }
  } else if (event.altKey && key === 'r') {
    event.preventDefault()
    readingMode.value = !readingMode.value
  }
}

async function importImages(files: File[]) {
  const current = session.value
  if (!files.length || importingImages.value) return
  const documentPath = current.path
  if (!documentPath || !current.baseline || current.missing) {
    error.value = '请先保存文档，再导入图片。'
    return
  }
  const generation = current.generation
  const stillCurrent = () => !disposed && current === session.value && current.path === documentPath && current.generation === generation
  importingImages.value = true
  error.value = ''
  const references: string[] = []
  const failures: string[] = []
  try {
    for (const file of files) {
      if (!stillCurrent()) return
      const name = file.name || '截图.png'
      try {
        const data = await fileBase64(file)
        if (!stillCurrent()) return
        const image = await mediaApi.add(documentPath, name, data)
        references.push(image.markdown)
      } catch (cause) { failures.push(name + '：' + message(cause)) }
    }
    if (!stillCurrent()) return
    if (references.length) {
      const inserted = insertImageReferences(current.text, editor.value?.selectionEnd ?? current.text.length, references)
      current.text = inserted.text
      await nextTick()
      if (!stillCurrent()) return
      editor.value?.focus()
      editor.value?.setSelectionRange(inserted.caret, inserted.caret)
      appStore.showToast('配图已导入。保存后 Markdown 引用才会写入文档。', 'success')
    }
    if (failures.length) error.value = failures.join('\n')
  } finally { importingImages.value = false }
}

function pasteImages(event: ClipboardEvent) {
  const files = Array.from(event.clipboardData?.files ?? []).filter(file => file.type.startsWith('image/'))
  if (files.length) {
    event.preventDefault()
    void importImages(files)
  }
}

function allowFileDrop(event: DragEvent) {
  if (event.dataTransfer?.types.includes('Files')) event.preventDefault()
}

function dropImages(event: DragEvent) {
  const files = Array.from(event.dataTransfer?.files ?? [])
  if (files.length) {
    event.preventDefault()
    void importImages(files)
  }
}

function selectImages(event: Event) {
  const input = event.target as HTMLInputElement
  void importImages(Array.from(input.files ?? []))
  input.value = ''
}

async function loadDirectories() {
  try { directories.value = (await contentApi.list()).directories.sort((a, b) => compareContentPaths(a.relative_path, b.relative_path)) }
  catch (cause) { checkError.value = message(cause) }
}

async function openDocument() {
  const previous = activeTab.value
  const tab = tabFromRoute()
  activeTab.value = tab
  if (previous !== tab) {
    error.value = ''
    checkError.value = ''
  }
  loading.value = false
  const current = tab.session
  if (!current.path) return
  if (current.baseline) {
    void checkExternal()
    return
  }
  const path = current.path
  const generation = ++current.generation
  loading.value = true
  try { current.load(await contentApi.read(path), generation) }
  catch (cause) { if (activeTab.value === tab && generation === current.generation) error.value = message(cause) }
  finally { if (activeTab.value === tab && generation === current.generation) loading.value = false }
}

function switchToTab(tab: EditorTab) {
  return router.push({ name: 'Editor', query: editorTabQuery(tab) })
}

function addTab() {
  return router.push({ name: 'Editor', query: { draft: newDraftId(), directory: directory.value } })
}

async function closeTab(tab: EditorTab) {
  if (leaveVisible.value || !(await confirmLeave([tab]))) return
  const selected = activeTab.value === tab
  removeEditorTab(tab)
  if (!selected) return
  const fallback = editorTabs.value.slice(-1)[0]
  if (fallback) await switchToTab(fallback)
  else await addTab()
}

function newPath(parent: string, name: string) {
  if (!name || name.includes('/') || name.includes('\\') || !/\.md$/i.test(name)) {
    throw new Error('请输入实际文件名，必须以 .md 结尾且不能包含目录分隔符')
  }
  return parent ? `${parent}/${name}` : name
}

function fillEmptyTitle() {
  if (!session.value.path && articleDocument.value) session.value.text = fillArticleTitle(session.value.text, filename.value)
}

watch([() => activeTab.value.id, articleDocument], ([id, article], [previous]) => {
  if (id !== previous || session.value.path) return
  const tab = activeTab.value
  const replaced = tab.session.replaceDraft(article ? createArticleTemplate(tab.startedAt) : '')
  tab.draftNotice = replaced ? '' : '已保留全部已编辑内容。普通文章请填写完整六字段；说明文档可保留当前头部。'
})

async function updateAddress() {
  if (session.value.path && route.query.id !== session.value.path) {
    await router.replace({ path: '/editor', query: { id: session.value.path } })
  }
}

async function handleSave(tab = activeTab.value): Promise<boolean> {
  const current = tab.session
  if ((tab === activeTab.value && loading.value) || current.saving || (current.path && !current.baseline)) return false
  error.value = ''
  const generation = current.generation
  try {
    const target = current.path ? undefined : newPath(tab.directory, tab.filename)
    const creating = !current.path
    const article = creating ? isArticleDocument(tab.filename, tab.purpose === 'article') : tab.purpose === 'auto' ? undefined : tab.purpose === 'article'
    if (creating && article) current.text = fillArticleTitle(current.text, tab.filename)
    const changed = current.dirty || !current.baseline
    await current.save(contentApi, target, article)
    if (generation !== current.generation) return false
    if (creating) tab.purpose = article ? 'article' : 'document'
    if (tab === activeTab.value && !leaveVisible.value) await updateAddress()
    appStore.showToast(changed ? '文档已保存' : '内容未变化，无需写入', 'success')
    return !current.dirty
  } catch (cause) {
    if (generation !== current.generation) return false
    error.value = (tab === activeTab.value ? '' : editorTabLabel(tab) + '：') + message(cause)
    if (tab === activeTab.value && cause instanceof ContentApiError && (cause.status === 409 || cause.status === 404)) await checkExternal()
    return false
  }
}

async function checkExternal() {
  const current = session.value
  if (document.hidden || loading.value) return
  const generation = current.generation
  const previousVersion = current.baseline?.version
  const scrollTop = editor.value?.scrollTop
  const selectionStart = editor.value?.selectionStart
  const selectionEnd = editor.value?.selectionEnd
  const selectionDirection = editor.value?.selectionDirection
  try {
    await current.check(contentApi)
    await nextTick()
    if ((current !== session.value || generation !== current.generation)) return
    checkError.value = ''
    if (editor.value && scrollTop !== undefined && previousVersion !== current.baseline?.version && current.externalUpdated && !current.dirty) {
      if (selectionStart !== undefined && selectionEnd !== undefined) editor.value.setSelectionRange(selectionStart, selectionEnd, selectionDirection)
      editor.value.scrollTop = scrollTop
    }
  } catch (cause) {
    if (current === session.value && generation === current.generation) checkError.value = `外部检查暂未成功，已保留当前文本：${message(cause)}`
  }
}

async function reloadFromDisk() {
  const current = session.value
  if (!current.path || current.saving || loading.value) return
  if (current.dirty && !window.confirm('放弃本地未保存修改，并重新读取磁盘文件？')) return
  const path = current.path
  const generation = ++current.generation
  loading.value = true
  error.value = ''
  try {
    current.load(await contentApi.read(path), generation)
    checkError.value = ''
    current.externalUpdated = false
  } catch (cause) { if (current === session.value && generation === current.generation) error.value = message(cause) }
  finally { if (current === session.value && generation === current.generation) loading.value = false }
}

async function copyLocal() {
  try {
    await navigator.clipboard.writeText(session.value.rawContent())
    appStore.showToast('本地修改已复制', 'success')
  } catch { appStore.showToast('复制失败，请在源码中全选复制', 'error') }
}

function openSaveAs() {
  const parts = (session.value.path || '').split('/')
  saveAsName.value = parts.pop() || filename.value
  saveAsDirectory.value = session.value.path ? parts.join('/') : directory.value
  saveAsVisible.value = true
}

async function saveAs() {
  const current = session.value
  const generation = current.generation
  error.value = ''
  try {
    await current.saveAs(contentApi, newPath(saveAsDirectory.value, saveAsName.value))
    if ((current !== session.value || generation !== current.generation)) return
    saveAsVisible.value = false
    await updateAddress()
    appStore.showToast('已另存为新文件', 'success')
  } catch (cause) { if (current === session.value && generation === current.generation) error.value = message(cause) }
}

function confirmLeave(tabs = editorTabs.value): Promise<boolean> {
  if (pendingLeave) return pendingLeave
  if (importingImages.value || tabs.some(tab => tab.session.saving)) {
    appStore.showToast('请等待当前保存或图片导入结束', 'warning')
    return Promise.resolve(false)
  }
  const dirty = tabs.filter(tab => tab.session.dirty)
  if (!dirty.length) return Promise.resolve(true)
  leaveTargets.value = dirty
  leaveVisible.value = true
  pendingLeave = new Promise(resolve => { resolveLeave = resolve })
  return pendingLeave
}

async function chooseLeave(action: 'save' | 'discard' | 'cancel') {
  if (leaveTargets.value.some(tab => tab.session.saving)) return
  if (action === 'save') {
    for (const tab of leaveTargets.value) {
      if (tab.session.dirty && !(await handleSave(tab))) return
    }
  } else if (action === 'discard') {
    leaveTargets.value.forEach(removeEditorTab)
  }
  leaveVisible.value = false
  resolveLeave?.(action !== 'cancel')
  resolveLeave = null
  pendingLeave = null
  leaveTargets.value = []
}

onBeforeRouteLeave(() => confirmLeave())
onBeforeRouteUpdate(() => {
  if (importingImages.value || editorTabs.value.some(tab => tab.session.saving)) return false
  return !leaveVisible.value
})

function beforeUnload(event: BeforeUnloadEvent) {
  if (editorTabs.value.some(tab => tab.session.dirty || tab.session.saving) || importingImages.value) {
    event.preventDefault()
    event.returnValue = ''
  }
}

function onFocus() { void loadDirectories(); void checkExternal() }

watch(() => [route.query.id, route.query.draft, route.query.directory], () => { void openDocument() }, { immediate: true })
onMounted(async () => {
  void loadDirectories()
  interval = setInterval(() => { void checkExternal() }, 2000)
  window.addEventListener('focus', onFocus)
  window.addEventListener('beforeunload', beforeUnload)
  window.addEventListener('keydown', editorShortcut)
  if (isTauri()) {
    try {
      const unlisten = await getCurrentWindow().onCloseRequested(async event => {
        if (!editorTabs.value.some(tab => tab.session.dirty || tab.session.saving) && !importingImages.value) return
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
  window.removeEventListener('keydown', editorShortcut)
  resolveLeave?.(false)
})
</script>

<template>
  <div>
    <div class="main-header">
      <div class="main-header-title">{{ session.path ? '编辑文档' : '新建文档' }}{{ session.dirty ? ' · 未保存' : '' }}</div>
      <div class="main-header-actions">
        <button class="btn btn-secondary btn-sm" @click="router.back()">返回</button>
        <button class="btn btn-secondary btn-sm" :disabled="session.saving || loading || importingImages || (!!session.path && !session.baseline)" @click="openSaveAs">另存为</button>
        <button class="btn btn-primary btn-sm" :disabled="session.saving || loading || (!!session.path && !session.baseline)" @click="handleSave()">{{ session.saving ? '保存中...' : '保存' }}</button>
      </div>
    </div>
    <div class="main-content">
      <div class="editor-tabs" aria-label="打开的文档">
        <div v-for="tab in editorTabs" :key="tab.id" class="editor-tab" :class="{ selected: tab === activeTab }">
          <button class="btn btn-ghost btn-sm" :aria-current="tab === activeTab ? 'true' : undefined"
            :title="tab.session.path || editorTabLabel(tab)" @click="switchToTab(tab)">
            {{ editorTabLabel(tab) }}{{ tab.session.dirty ? ' •' : '' }}
          </button>
          <button class="btn btn-ghost btn-sm" :aria-label="'关闭 ' + editorTabLabel(tab)" @click="closeTab(tab)">×</button>
        </div>
        <button class="btn btn-secondary btn-sm" type="button" @click="addTab">新标签页</button>
      </div>
      <EditorQuickSwitch ref="quickSwitch" :path="session.path" @navigate="path => router.push({ name: 'Editor', query: { id: path } })" />
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
          <button class="btn btn-secondary btn-sm" :disabled="session.saving || loading || importingImages" @click="reloadFromDisk">放弃本地修改并重载</button>
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
      <ArticleForm v-if="!readingMode && !loading && (session.baseline || articleDocument)" :key="activeTab.id + ':' + session.generation" :text="session.text"
        @apply="(before, after) => { if (session.text === before) session.text = after }" />
      <div class="card" style="padding: 0; overflow: hidden;">
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 8px 12px; border-bottom: 1px solid var(--border-subtle);">
          <span style="font-size: 12px; color: var(--text-secondary);">{{ loading ? '读取中...' : 'Markdown 源码编辑' }}</span>
          <span style="font-size: 12px; color: var(--text-tertiary); overflow-wrap: anywhere;">{{ session.path || '尚未创建' }}</span>
          <button class="btn btn-secondary btn-sm" type="button" :aria-pressed="readingMode" title="Alt+R" @click="readingMode = !readingMode">
            {{ readingMode ? '返回编辑' : '阅读模式' }}
          </button>
          <button v-if="!readingMode" class="btn btn-secondary btn-sm" :aria-pressed="showPreview" @click="showPreview = !showPreview">{{ showPreview ? '隐藏预览' : '显示预览' }}</button>
          <input ref="imagePicker" type="file" multiple hidden :accept="imageExtensions" @change="selectImages" />
          <button type="button" class="btn btn-secondary btn-sm" :disabled="readingMode || !session.baseline || session.missing || importingImages" @click="imagePicker?.click()">
            {{ importingImages ? '导入中…' : '插入图片' }}
          </button>
          <RouterLink v-if="session.path && session.baseline" class="btn btn-secondary btn-sm" :to="{ name: 'Media', query: { document: session.path } }">配图</RouterLink>
          <button v-if="session.path" class="btn btn-secondary btn-sm" :disabled="session.saving || loading" @click="checkExternal">检查外部变化</button>
          <button v-if="session.path && !session.baseline" class="btn btn-secondary btn-sm" @click="reloadFromDisk">重试读取</button>
        </div>
        <div v-if="!readingMode" class="markdown-toolbar" role="group" aria-label="Markdown 工具栏">
          <button v-for="item in markdownCommands" :key="item.action" class="btn btn-ghost btn-sm" type="button"
            :title="item.shortcut || item.label" :disabled="loading || (!!session.path && !session.baseline)"
            @mousedown.prevent @click="applyCommand(item.action)">{{ item.label }}</button>
        </div>
        <div class="editor-panes" :class="{ split: showPreview && !readingMode }">
          <textarea v-if="!readingMode" ref="editor" v-model="session.text" class="editor-content" :disabled="loading || (!!session.path && !session.baseline)" aria-label="完整 Markdown 源码" spellcheck="false" @paste="pasteImages" @dragover="allowFileDrop" @drop="dropImages" />
          <MarkdownPreview v-if="showPreview || readingMode" :text="session.text" :document-directory="previewDirectory"
            @open-document="path => router.push({ path: '/editor', query: { id: path } })" />
        </div>
      </div>
      <DocumentBacklinks v-if="session.path && session.baseline" :path="session.path" />
    </div>
    <div v-if="leaveVisible" class="editor-modal-backdrop">
      <section role="dialog" aria-modal="true" aria-labelledby="leave-title" class="card editor-dialog">
        <h3 id="leave-title">有未保存修改</h3><p>保存成功后离开，或明确放弃本地修改。</p>
        <ul><li v-for="tab in leaveTargets" :key="tab.id">{{ editorTabLabel(tab) }}</li></ul>
        <p v-if="error" role="alert">{{ error }}</p>
        <div class="editor-dialog-actions">
          <button class="btn btn-secondary" :disabled="leaveTargets.some(tab => tab.session.saving)" @click="chooseLeave('cancel')">取消</button>
          <button class="btn btn-secondary" :disabled="leaveTargets.some(tab => tab.session.saving)" @click="chooseLeave('discard')">放弃并离开</button>
          <button class="btn btn-primary" :disabled="leaveTargets.some(tab => tab.session.saving)" @click="chooseLeave('save')">{{ leaveTargets.some(tab => tab.session.saving) ? '保存中...' : '保存并离开' }}</button>
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
.editor-tabs { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.editor-tab { display: inline-flex; align-items: center; max-width: 240px; border: 1px solid var(--border-subtle); border-radius: 6px; }
.editor-tab.selected { border-color: var(--text-secondary); }
.editor-tab button:first-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.markdown-toolbar { display: flex; flex-wrap: wrap; gap: 4px; padding: 6px 12px; border-bottom: 1px solid var(--border-subtle); }
.editor-content { width: 100%; min-height: 500px; padding: 16px; font-family: var(--font-mono); font-size: 13px; line-height: 1.7; border: none; outline: none; resize: vertical; background: var(--bg-panel); color: var(--text-primary); }
.editor-panes.split { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
.editor-panes.split .editor-content { border-right: 1px solid var(--border-subtle); }
@media (max-width: 960px) { .editor-panes.split { grid-template-columns: 1fr; } }
.editor-modal-backdrop { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 24px; background: rgba(0, 0, 0, 0.4); }
.editor-dialog { width: min(560px, 100%); max-height: 90vh; overflow: auto; background: var(--bg-panel); }
.editor-dialog label { display: block; margin: 12px 0; }
.editor-dialog-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 20px; }
.editor-comparison { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 16px; margin-top: 12px; }
.editor-comparison pre { max-height: 320px; overflow: auto; white-space: pre-wrap; overflow-wrap: anywhere; font-family: var(--font-mono); }
@media (max-width: 720px) { .editor-comparison { grid-template-columns: 1fr; } }
</style>
