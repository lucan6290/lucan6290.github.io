<script setup lang="ts">
import { inject } from 'vue'
import { useAppStore, type ThemeMode } from '@/stores/app'
import { workspaceControlsKey } from '@/utils/workspaceControls'
import DesktopUpdate from '@/components/DesktopUpdate.vue'
import SiteActions from '@/components/SiteActions.vue'

const appStore = useAppStore()
const controls = inject(workspaceControlsKey)
const modes: { value: ThemeMode; label: string }[] = [{ value: 'system', label: '跟随系统' }, { value: 'light', label: '浅色' }, { value: 'dark', label: '深色' }]
</script>

<template>
  <div>
    <div class="main-header"><div class="main-header-title">设置</div></div>
    <div class="main-content settings-cards">
      <section class="card">
        <h3>当前内容库</h3>
        <p class="settings-root">{{ controls?.root.value || '连接中…' }}</p>
        <button v-if="controls?.available" type="button" class="btn btn-secondary" :disabled="controls.busy.value" @click="controls.select">
          {{ controls.busy.value ? '正在连接…' : '更换博客目录' }}
        </button>
        <p v-else>在原生桌面应用中可更换博客目录。</p>
        <p v-if="controls?.error.value" role="alert" class="settings-error">{{ controls.error.value }}</p>
      </section>
      <section class="card">
        <h3>主题</h3>
        <label v-for="mode in modes" :key="mode.value" class="theme-option">
          <input type="radio" name="theme" :value="mode.value" :checked="appStore.themeMode === mode.value" @change="appStore.setTheme(mode.value)" />{{ mode.label }}
        </label>
      </section>
      <section class="card">
        <h3>站点预览与构建</h3>
        <SiteActions :document-path="null" />
      </section>
      <DesktopUpdate />
    </div>
  </div>
</template>

<style scoped>
.settings-cards { display: grid; gap: 16px; }
.settings-root { overflow-wrap: anywhere; }
.settings-error { white-space: pre-wrap; color: var(--status-error); }
.theme-option { display: inline-flex; align-items: center; gap: 6px; margin-inline-end: 24px; }
</style>
