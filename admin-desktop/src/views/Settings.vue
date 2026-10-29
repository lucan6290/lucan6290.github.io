<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { contentApi } from '@/api/content'
import { useAppStore, type ThemeMode } from '@/stores/app'
const appStore = useAppStore()
const contentRoot = ref('')
const error = ref('')
const modes: { value: ThemeMode; label: string }[] = [{ value: 'system', label: '跟随系统' }, { value: 'light', label: '浅色' }, { value: 'dark', label: '深色' }]
onMounted(async () => {
  try { contentRoot.value = (await contentApi.health()).content_root }
  catch (cause) { error.value = cause instanceof Error ? cause.message : '连接失败' }
})
</script>
<template>
  <div>
    <div class="main-header"><div class="main-header-title">设置</div></div>
    <div class="main-content">
      <div class="card"><h3>当前内容库</h3><p style="overflow-wrap: anywhere;">{{ contentRoot || error || '连接中…' }}</p><p>桌面端直接读写 Markdown。外部修改会在恢复窗口焦点或检查文件版本时更新。</p></div>
      <div class="card" style="margin-top: 16px;"><h3>主题</h3><label v-for="mode in modes" :key="mode.value" style="display: inline-flex; align-items: center; gap: 6px; margin-right: 24px;"><input type="radio" name="theme" :value="mode.value" :checked="appStore.themeMode === mode.value" @change="appStore.setTheme(mode.value)" />{{ mode.label }}</label></div>
      <div class="card" style="margin-top: 16px;"><h3>辅助功能适配进度</h3><p>图片管理、AI 写作、站点预览与构建、Git 发布将在后续阶段适配。</p><p>当前目录和 Markdown 是导航与标签的来源，无需同步旧站侧边栏或注册表。</p></div>
    </div>
  </div>
</template>
