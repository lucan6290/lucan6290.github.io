<script setup lang="ts">
import { ref } from 'vue'
import { invoke, isTauri } from '@tauri-apps/api/core'
import { revealItemInDir } from '@tauri-apps/plugin-opener'

interface PreviewResult { url: string; owned: boolean; log_path: string | null }
interface BuildResult { exit_code: number | null; output_dir: string | null; log_path: string; log_tail: string }

const props = defineProps<{ documentPath: string | null }>()
const desktop = isTauri()
const busy = ref<'preview' | 'build' | null>(null)
const preview = ref<PreviewResult | null>(null)
const build = ref<BuildResult | null>(null)
const error = ref('')

async function run(action: 'preview' | 'build') {
  if (!desktop || busy.value) return
  error.value = ''
  busy.value = action
  try {
    if (action === 'preview') {
      preview.value = null
      preview.value = await invoke<PreviewResult>('open_site_preview', { documentPath: props.documentPath })
    } else {
      build.value = null
      build.value = await invoke<BuildResult>('build_blog_site')
    }
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : String(cause)
  } finally {
    busy.value = null
  }
}

async function locate(path: string) {
  try { await revealItemInDir(path) }
  catch (cause) { error.value = cause instanceof Error ? cause.message : String(cause) }
}
</script>

<template>
  <div class="site-actions">
    <div class="site-buttons">
      <button type="button" class="btn btn-secondary" :disabled="!desktop || !!busy" @click="run('preview')">
        {{ busy === 'preview' ? '启动站点预览…' : documentPath ? '在站点预览本文' : '打开站点首页' }}
      </button>
      <button type="button" class="btn btn-secondary" :disabled="!desktop || !!busy" @click="run('build')">
        {{ busy === 'build' ? '生产构建中…' : '生产构建' }}
      </button>
    </div>
    <p v-if="!desktop">站点预览和生产构建可在桌面应用中使用。</p>
    <p v-else-if="documentPath">站点预览使用已保存的文档。</p>
    <p v-if="error" class="site-error" role="alert">{{ error }}</p>
    <div v-if="preview" role="status">
      <p>已打开 {{ preview.owned ? '桌面应用启动的' : '当前工作区已有的' }}站点预览。<code>{{ preview.url }}</code></p>
      <button v-if="preview.log_path" type="button" class="btn btn-secondary" @click="locate(preview.log_path)">定位预览日志</button>
    </div>
    <div v-if="build">
      <p role="status" :class="{ 'site-error': !build.output_dir }">
        {{ build.output_dir ? '构建成功' : build.exit_code === 0 ? '构建结束，未找到完整产物' : '构建失败' }}（退出码 {{ build.exit_code ?? '未知' }}）
      </p>
      <p v-if="build.output_dir"><code>{{ build.output_dir }}</code></p>
      <div class="site-buttons">
        <button v-if="build.output_dir" type="button" class="btn btn-secondary" @click="locate(build.output_dir)">定位构建产物</button>
        <button type="button" class="btn btn-secondary" @click="locate(build.log_path)">定位构建日志</button>
      </div>
      <details v-if="build.log_tail"><summary>构建日志末尾</summary><pre>{{ build.log_tail }}</pre></details>
    </div>
  </div>
</template>

<style scoped>
.site-actions { display: grid; gap: 8px; overflow-wrap: anywhere; }
.site-actions p { margin: 0; }
.site-actions details { margin-top: 8px; }
.site-actions pre { max-height: 240px; overflow: auto; white-space: pre-wrap; }
.site-buttons { display: flex; flex-wrap: wrap; gap: 8px; }
.site-error { color: var(--status-error); }
</style>
