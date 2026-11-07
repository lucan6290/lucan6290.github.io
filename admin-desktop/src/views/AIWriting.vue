<script setup lang="ts">
import { computed, onMounted, ref, shallowRef } from 'vue'
import { aiErrorMessage, aiWritingApi } from '@/api/aiWriting'

type SavedSettings = Awaited<ReturnType<typeof aiWritingApi.settings>>
type KeyAction = 'keep' | 'session' | 'windows' | 'clear'

const settings = shallowRef<SavedSettings>()
const baseUrl = ref('')
const model = ref('')
const key = ref('')
const keyAction = ref<KeyAction>('keep')
const busy = ref<'loading' | 'saving' | 'testing' | ''>('loading')
const message = ref('')
const error = ref('')
const needsKey = computed(() => keyAction.value === 'session' || keyAction.value === 'windows')
const keyStatus = computed(() => {
  if (settings.value?.key_mode === 'session') return '本次会话已配置密钥'
  if (settings.value?.key_mode === 'windows') return '已由 Windows 保护并保存密钥'
  return '未配置密钥'
})

function useSettings(value: SavedSettings) {
  settings.value = value
  baseUrl.value = value.base_url
  model.value = value.model
  keyAction.value = 'keep'
  key.value = ''
}

onMounted(async () => {
  try {
    useSettings(await aiWritingApi.settings())
  } catch (cause) {
    error.value = aiErrorMessage(cause, '无法读取 AI 设置，请检查本机内容服务。')
  } finally {
    busy.value = ''
  }
})

async function save() {
  busy.value = 'saving'
  message.value = ''
  error.value = ''
  try {
    useSettings(await aiWritingApi.saveSettings({
      base_url: baseUrl.value.trim(),
      model: model.value.trim(),
      ...(keyAction.value === 'keep' ? {} : { key_mode: keyAction.value }),
      ...(needsKey.value ? { api_key: key.value } : {})
    }))
    message.value = '已保存 AI 设置。'
  } catch (cause) {
    error.value = aiErrorMessage(cause, '无法保存 AI 设置。')
  } finally {
    busy.value = ''
  }
}

async function testConnection() {
  busy.value = 'testing'
  message.value = ''
  error.value = ''
  try {
    await aiWritingApi.test()
    message.value = '连接成功，模型已返回响应。'
  } catch (cause) {
    error.value = aiErrorMessage(cause, '无法测试连接，请检查本机内容服务。')
  } finally {
    busy.value = ''
  }
}
</script>

<template>
  <div>
    <div class="main-header"><div class="main-header-title">AI 写作</div></div>
    <div class="main-content">
      <form class="card ai-settings" @submit.prevent="save">
        <h3>模型服务</h3>
        <p>配置 OpenAI 兼容服务后，可在编辑器生成或改写正文并查看对照。连接测试会发送一条固定提示。</p>
        <label>
          服务基础地址
          <input v-model="baseUrl" class="input" placeholder="https://api.openai.com/v1" autocomplete="off" spellcheck="false" maxlength="2048" required :disabled="!!busy" aria-describedby="ai-url-hint" />
        </label>
        <p id="ai-url-hint" class="ai-hint">使用 HTTPS，或填写不需要密钥的本机 HTTP 回环地址，例如 http://127.0.0.1:11434/v1。</p>
        <label>
          模型 ID
          <input v-model="model" class="input" placeholder="填入服务端提供的模型 ID" autocomplete="off" spellcheck="false" maxlength="200" required :disabled="!!busy" />
        </label>
        <label>
          API 密钥
          <select v-model="keyAction" class="select" :disabled="!!busy" @change="key = ''">
            <option value="keep">保留当前状态</option>
            <option value="session">输入新密钥，仅本次会话</option>
            <option v-if="settings?.supports_windows_storage" value="windows">输入新密钥，由 Windows 保护并保存</option>
            <option v-if="settings?.key_mode && settings.key_mode !== 'none'" value="clear">清除密钥</option>
          </select>
        </label>
        <label v-if="needsKey">
          新密钥
          <input v-model="key" class="input" type="password" autocomplete="new-password" maxlength="2048" required :disabled="!!busy" />
        </label>
        <p class="ai-hint">{{ keyStatus }}。修改服务地址会清除旧地址的密钥。</p>
        <div class="ai-actions">
          <button class="btn btn-primary" type="submit" :disabled="!!busy">{{ busy === 'saving' ? '正在保存…' : '保存设置' }}</button>
          <button class="btn btn-secondary" type="button" :disabled="!!busy || !settings?.base_url" @click="testConnection">
            {{ busy === 'testing' ? '正在测试…' : '测试已保存的连接' }}
          </button>
        </div>
        <p v-if="error" class="ai-error" role="alert">{{ error }}</p>
        <p v-if="message || busy === 'loading'" role="status">{{ message || '正在读取设置…' }}</p>
      </form>
    </div>
  </div>
</template>

<style scoped>
.ai-settings { display: grid; gap: 12px; max-width: 660px; }
.ai-settings h3, .ai-settings p { margin: 0; }
.ai-settings label { display: grid; gap: 6px; }
.ai-hint { color: var(--text-secondary); }
.ai-error { color: var(--status-error); }
.ai-actions { display: flex; flex-wrap: wrap; gap: 8px; }
</style>