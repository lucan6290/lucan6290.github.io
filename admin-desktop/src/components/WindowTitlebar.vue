<script setup lang="ts">
import { invoke } from '@tauri-apps/api/core'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

async function handleMinimize() {
  try {
    await invoke('minimize_window')
  } catch {
    // 非 Tauri 环境（浏览器调试）忽略
  }
}

async function handleMaximize() {
  try {
    await invoke('maximize_window')
  } catch {
    // ignore
  }
}

async function handleClose() {
  try {
    await invoke('close_window')
  } catch {
    // ignore
  }
}
</script>

<template>
  <div class="window-titlebar">
    <!-- 左侧：侧边栏折叠按钮 + 品牌 -->
    <div class="titlebar-left">
      <button class="window-control-btn" style="width: 28px;" @click="appStore.toggleSidebar" title="折叠侧边栏">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M2 4h12M2 8h12M2 12h12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </button>
    </div>

    <!-- 中间：应用标题 -->
    <div class="titlebar-center">
      箓川码笺 · 管理端
    </div>

    <!-- 右侧：窗口控制按钮 -->
    <div class="titlebar-right">
      <button class="window-control-btn" @click="handleMinimize" title="最小化">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M2 7h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </button>
      <button class="window-control-btn" @click="handleMaximize" title="最大化">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <rect x="2.5" y="2.5" width="9" height="9" rx="1" stroke="currentColor" stroke-width="1.5"/>
        </svg>
      </button>
      <button class="window-control-btn close" @click="handleClose" title="关闭">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M3 3l8 8M11 3l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </button>
    </div>
  </div>
</template>
