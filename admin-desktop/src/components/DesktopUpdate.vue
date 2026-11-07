<script setup lang="ts">
import { invoke, isTauri } from '@tauri-apps/api/core'
import { computed, onMounted, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

const enabled = ref(false)
const current = ref('')
const candidate = ref<string | null>(null)
const ready = ref(false)
const busy = ref<'check' | 'download' | 'install' | null>(null)
const status = ref('正在读取更新渠道…')
const error = ref('')
const message = computed(() => error.value || status.value)

onMounted(async () => {
  if (!isTauri()) {
    status.value = '浏览器中不可用，请使用已配置更新渠道的 Windows 安装版。'
    return
  }
  try {
    const result = await invoke<{ enabled: boolean; version: string }>('get_desktop_update_status')
    enabled.value = result.enabled
    current.value = result.version
    status.value = result.enabled ? '可以手动检查新版本。' : '此构建未配置正式更新渠道。'
  } catch (cause) {
    error.value = `无法读取更新状态：${String(cause)}`
  }
})

onBeforeRouteLeave(() => busy.value !== 'install')

async function checkUpdate() {
  if (!enabled.value || busy.value) return
  busy.value = 'check'
  candidate.value = null
  ready.value = false
  error.value = ''
  status.value = '正在检查更新…'
  try {
    candidate.value = await invoke<string | null>('check_desktop_update')
    status.value = candidate.value ? `发现版本 ${candidate.value}。` : '当前已是最新版本。'
  } catch (cause) {
    error.value = `检查更新失败：${String(cause)}`
  } finally {
    busy.value = null
  }
}

async function downloadUpdate() {
  if (!candidate.value || busy.value) return
  busy.value = 'download'
  error.value = ''
  status.value = '正在下载并验证更新签名…'
  try {
    await invoke('download_desktop_update', { version: candidate.value })
    ready.value = true
    status.value = `已验证版本 ${candidate.value}。安装时应用将退出并重新打开。`
  } catch (cause) {
    error.value = `下载或验证更新失败：${String(cause)}`
  } finally {
    busy.value = null
  }
}

async function installUpdate() {
  if (!candidate.value || !ready.value || busy.value) return
  busy.value = 'install'
  error.value = ''
  status.value = '正在启动安装程序…'
  try {
    await invoke('install_desktop_update', { version: candidate.value })
  } catch (cause) {
    error.value = `启动安装程序失败：${String(cause)}`
  } finally {
    busy.value = null
  }
}
</script>

<template>
  <section class="card desktop-update" aria-label="应用更新">
    <h3>应用更新</h3>
    <p v-if="current">当前版本 {{ current }}</p>
    <p role="status">{{ message }}</p>
    <div v-if="enabled" class="desktop-update-actions">
      <button type="button" class="btn btn-secondary btn-sm" :disabled="!!busy" @click="checkUpdate">检查更新</button>
      <button v-if="candidate && !ready" type="button" class="btn btn-primary btn-sm" :disabled="!!busy" @click="downloadUpdate">下载更新</button>
      <button v-if="ready" type="button" class="btn btn-primary btn-sm" :disabled="!!busy" @click="installUpdate">安装并重启</button>
    </div>
  </section>
</template>

<style scoped>
.desktop-update { margin-top: 16px; }
.desktop-update p { overflow-wrap: anywhere; }
.desktop-update-actions { display: flex; flex-wrap: wrap; gap: 8px; }
</style>
