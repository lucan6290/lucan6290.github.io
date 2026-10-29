<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { invoke, isTauri } from '@tauri-apps/api/core'
import { contentApi, setContentConnection } from '@/api/content'
import { useAppStore } from '@/stores/app'
import WindowTitlebar from '@/components/WindowTitlebar.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import ToastContainer from '@/components/ToastContainer.vue'
interface Connection { base_url: string; token: string; content_root?: string }
const appStore = useAppStore()
const connected = ref(false)
const connecting = ref(false)
const error = ref('')
const token = ref('')
const desktop = isTauri()
async function connect(connection: Connection) {
  setContentConnection(connection.base_url, connection.token)
  const health = await contentApi.health()
  if (health.service !== 'xiaocancoding-content' || health.api_version !== 1) throw new Error('18000 端口不是当前内容服务。')
  if (connection.content_root && connection.content_root !== health.content_root) throw new Error('内容根目录已变化，请重新连接当前项目。')
  await contentApi.list()
  appStore.backendReady = true
  appStore.backendPort = 18000
  if (!desktop) sessionStorage.setItem('content-session', JSON.stringify({ ...connection, content_root: health.content_root }))
  connected.value = true
  token.value = ''
}
async function reconnect() {
  connecting.value = true
  error.value = ''
  try {
    await connect(desktop ? await invoke<Connection>('get_backend_connection') : { base_url: 'http://127.0.0.1:18000', token: token.value.trim() })
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : String(cause)
    appStore.backendReady = false
  } finally { connecting.value = false }
}
onMounted(async () => {
  appStore.init()
  if (desktop) { await reconnect(); return }
  const stored = sessionStorage.getItem('content-session')
  if (!stored) return
  connecting.value = true
  try { await connect(JSON.parse(stored) as Connection) }
  catch (cause) { sessionStorage.removeItem('content-session'); error.value = cause instanceof Error ? cause.message : String(cause) }
  finally { connecting.value = false }
})
</script>
<template>
  <div class="desktop-shell" :class="{ 'sidebar-collapsed': appStore.sidebarCollapsed }">
    <WindowTitlebar /><AppSidebar />
    <main class="desktop-main">
      <router-view v-if="connected" />
      <div v-else class="main-content" style="max-width: 680px; margin: 60px auto;">
        <div class="card">
          <h2>连接本地内容库</h2><p>文档直接保存在当前项目的 frontend/content，供桌面端、编辑器和 AI 共同维护。</p>
          <p v-if="error" role="alert" style="color: var(--status-error); white-space: pre-wrap;">{{ error }}</p>
          <form v-if="!desktop" @submit.prevent="reconnect">
            <label for="session-token">本地会话令牌</label><p style="font-size: 13px; color: var(--text-secondary);">启动内容后端后，使用本次会话的令牌连接；桌面应用会自动连接。</p>
            <input id="session-token" v-model="token" class="input" type="password" autocomplete="off" required />
            <button class="btn btn-primary" style="margin-top: 12px;" :disabled="connecting">{{ connecting ? '连接中…' : '连接' }}</button>
          </form>
          <button v-else class="btn btn-primary" :disabled="connecting" @click="reconnect">{{ connecting ? '启动内容服务中…' : '重新连接' }}</button>
        </div>
      </div>
    </main><ToastContainer />
  </div>
</template>
