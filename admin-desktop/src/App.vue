<script setup lang="ts">
import { onMounted, onUnmounted, provide, ref } from 'vue'
import { invoke, isTauri } from '@tauri-apps/api/core'
import { open } from '@tauri-apps/plugin-dialog'
import { contentApi, setContentConnection } from '@/api/content'
import { useAppStore } from '@/stores/app'
import { clearEditorTabs, editorTabs } from '@/utils/editorTabs'
import { openFavorites } from '@/utils/editorFavorites'
import { formatWindowsPathsForDisplay, workspaceControlsKey } from '@/utils/workspaceControls'
import WindowTitlebar from '@/components/WindowTitlebar.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import ToastContainer from '@/components/ToastContainer.vue'
interface Connection { base_url: string; token: string; content_root?: string }
const appStore = useAppStore()
const connected = ref(false)
const workspace = ref('')
const workspaceError = ref('')
const connecting = ref(false)
const error = ref('')
const token = ref('')
const needsDirectory = ref(false)
const recoveryError = ref('')
const desktop = isTauri()
const maxRecoveryAttempts = 2
let recoveryAttempts = 0
let checkingConnection = false
let healthTimer: ReturnType<typeof setInterval> | undefined
async function connect(connection: Connection) {
  setContentConnection(connection.base_url, connection.token)
  const health = await contentApi.health()
  if (health.service !== 'xiaocancoding-content' || health.api_version !== 1) throw new Error('本机端口不是当前内容服务。')
  if (connection.content_root && connection.content_root !== health.content_root) throw new Error('内容根目录已变化，请重新连接当前项目。')
  await contentApi.list()
  if (workspace.value !== health.content_root) {
    clearEditorTabs()
    openFavorites(health.content_root)
    workspace.value = health.content_root
  }
  appStore.backendReady = true
  appStore.backendPort = Number(new URL(connection.base_url).port)
  if (!desktop) sessionStorage.setItem('content-session', JSON.stringify({ ...connection, content_root: health.content_root }))
  connected.value = true
  token.value = ''
}

async function recoverConnection(manual = false) {
  if (connecting.value) return
  connecting.value = true
  recoveryError.value = ''
  recoveryAttempts = manual ? maxRecoveryAttempts : recoveryAttempts + 1
  try {
    const connection = await invoke<Connection | null>('get_backend_connection', { recover: !manual })
    if (!connection || connection.content_root !== workspace.value) throw new Error('当前工作区的内容服务尚未恢复。')
    // 原生层已验证项目根和令牌。只换连接，避免卸载编辑器或重放写入。
    setContentConnection(connection.base_url, connection.token)
    appStore.backendPort = Number(new URL(connection.base_url).port)
    appStore.backendReady = true
  } catch (cause) {
    appStore.backendReady = false
    recoveryError.value = cause instanceof Error ? cause.message : String(cause)
  } finally { connecting.value = false }
}

async function monitorConnection() {
  if (!connected.value || connecting.value || checkingConnection) return
  checkingConnection = true
  let failed = false
  try {
    // 探测鉴权也能发现同一端口的后端已重启、令牌已变更。
    const health = await contentApi.health(2000)
    if (health.service !== 'xiaocancoding-content' || health.api_version !== 1 || health.content_root !== workspace.value) throw new Error('内容服务身份已变化。')
    await contentApi.probe(2000)
    if (connecting.value) return
    appStore.backendReady = true
    recoveryAttempts = 0
    recoveryError.value = ''
  } catch {
    if (connecting.value) return
    appStore.backendReady = false
    failed = true
  } finally { checkingConnection = false }
  if (failed && recoveryAttempts < maxRecoveryAttempts) await recoverConnection()
}
async function reconnect(projectRoot?: string) {
  connecting.value = true
  error.value = ''
  try {
    const connection = desktop
      ? await invoke<Connection | null>('get_backend_connection', { projectRoot })
      : { base_url: 'http://127.0.0.1:18000', token: token.value.trim() }
    needsDirectory.value = !connection
    if (connection) await connect(connection)
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : String(cause)
    appStore.backendReady = false
  } finally { connecting.value = false }
}
async function chooseDirectory() {
  try {
    const selected = await open({ directory: true, multiple: false, title: '选择博客目录' })
    if (selected) await reconnect(selected)
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : String(cause)
  }
}
async function switchWorkspace() {
  if (!desktop || connecting.value || editorTabs.value.some(tab => tab.session.dirty || tab.session.saving)) return
  const selected = await open({ directory: true, multiple: false, title: '更换博客目录' }).catch(cause => {
    workspaceError.value = cause instanceof Error ? cause.message : String(cause)
    return null
  })
  if (!selected || typeof selected !== 'string' || connecting.value || editorTabs.value.some(tab => tab.session.dirty || tab.session.saving)) return
  connecting.value = true
  workspaceError.value = ''
  recoveryAttempts = 0
  try {
    const next = await invoke<Connection>('switch_blog_workspace', { projectRoot: selected })
    await connect(next)
  } catch (cause) {
    const message = cause instanceof Error ? cause.message : String(cause)
    try {
      const previous = await invoke<Connection | null>('get_backend_connection')
      if (!previous) throw new Error('没有已连接的工作区')
      await connect(previous)
      workspaceError.value = message
    } catch (restore) {
      error.value = message + '\n重新连接失败：' + (restore instanceof Error ? restore.message : String(restore))
      appStore.backendReady = false
      connected.value = false
    }
  } finally { connecting.value = false }
}

provide(workspaceControlsKey, {
  available: desktop, root: workspace, busy: connecting, error: workspaceError, select: switchWorkspace,
})

onMounted(async () => {
  appStore.init()
  if (desktop) { healthTimer = setInterval(() => { void monitorConnection() }, 3000); await reconnect(); return }
  const stored = sessionStorage.getItem('content-session')
  if (!stored) return
  connecting.value = true
  try { await connect(JSON.parse(stored) as Connection) }
  catch (cause) { sessionStorage.removeItem('content-session'); error.value = cause instanceof Error ? cause.message : String(cause) }
  finally { connecting.value = false }
})
onUnmounted(() => clearInterval(healthTimer))
</script>
<template>
  <div class="desktop-shell" :class="{ 'sidebar-collapsed': appStore.sidebarCollapsed }">
    <WindowTitlebar /><AppSidebar />
    <main class="desktop-main">
      <div v-if="desktop && connected && !appStore.backendReady" class="backend-notice" role="status">
        <span>{{ connecting ? '正在恢复内容服务…' : '内容服务未连接。未保存的编辑仍保留。' }}</span>
        <button v-if="!connecting" class="btn btn-secondary" :title="recoveryError" @click="recoverConnection(true)">重新连接</button>
      </div>
      <router-view v-if="connected" :key="workspace" />
      <div v-else class="main-content" style="max-width: 680px; margin: 60px auto;">
        <div class="card">
          <h2>连接本地内容库</h2><p>文档直接保存在当前项目的 frontend/content，供桌面端、编辑器和 AI 共同维护。</p>
          <p v-if="error" role="alert" style="color: var(--status-error); white-space: pre-wrap;">{{ formatWindowsPathsForDisplay(error) }}</p>
          <form v-if="!desktop" @submit.prevent="reconnect()">
            <label for="session-token">本地会话令牌</label><p style="font-size: 13px; color: var(--text-secondary);">启动内容后端后，使用本次会话的令牌连接；桌面应用会自动连接。</p>
            <input id="session-token" v-model="token" class="input" type="password" autocomplete="off" required />
            <button class="btn btn-primary" style="margin-top: 12px;" :disabled="connecting">{{ connecting ? '连接中…' : '连接' }}</button>
          </form>
          <div v-else class="workspace-actions">
            <p v-if="needsDirectory">选择博客仓库根目录或其中的 frontend/content。</p>
            <button class="btn btn-primary" :disabled="connecting" @click="chooseDirectory">{{ connecting ? '启动内容服务中…' : '选择博客目录' }}</button>
            <button v-if="!needsDirectory && error" class="btn btn-secondary" :disabled="connecting" @click="reconnect()">重新连接</button>
          </div>
        </div>
      </div>
    </main><ToastContainer />
  </div>
</template>

<style scoped>
.workspace-actions button + button { margin-left: 8px; }
.backend-notice { padding: 8px 16px; display: flex; align-items: center; gap: 12px; }
</style>
