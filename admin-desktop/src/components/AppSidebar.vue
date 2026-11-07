<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { useAppStore, type ThemeMode } from '@/stores/app'
import type { RouteRecordRaw } from 'vue-router'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()

// 导航图标（内联 SVG path data）
const icons: Record<string, string> = {
  dashboard: 'M3 3h7v7H3V3zm11 0h7v7h-7V3zM3 14h7v7H3v-7zm11 0h7v7h-7v-7z',
  posts: 'M4 4h16v3H4V4zm0 6h16v3H4v-3zm0 6h10v3H4v-3z',
  editor: 'M3 5h18v14H3V5zm2 2v10h14V7H5zm2 2h6v2H7V9z',
  registry: 'M4 6h16M4 10h16M4 14h16M4 18h16',
  media: 'M3 5h18v14H3V5zm2 2v10h14V7H5zm2 7l3-4 3 3 2-2 3 3H7z',
  ai: 'M12 2a7 7 0 1 1 0 14 7 7 0 0 1 0-14zm0 3l1 3 3 1-3 1-1 3-1-3-3-1 3-1 1-3z',
  graph: 'M6 6l6 6m6-6l-6 6m0 0v7M4 4h4v4H4zM16 4h4v4h-4zM10 18h4v4h-4z',
  git: 'M6 5a2 2 0 1 0 0 4a2 2 0 0 0 0-4zm0 10a2 2 0 1 0 0 4a2 2 0 0 0 0-4zm12-8a2 2 0 1 0 0 4a2 2 0 0 0 0-4zM6 9v6m12-4c0 5-5 6-10 6',
  settings: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zm8 4l-2-1-1-3 1-1-1-1-3 1-1-2-1-2 1-2 1-3 1-1 1 1 3 1 1-1 2 1 2 2-1 1 1-1 3 1 1 2-1 1z'
}

const navRoutes = router.options.routes.map((r: RouteRecordRaw) => ({
  path: r.path,
  name: r.name as string,
  title: (r.meta?.title as string) || (r.name as string),
  icon: (r.meta?.icon as string) || 'dashboard'
}))

function isActive(path: string): boolean {
  return route.path === path
}

function cycleTheme() {
  const modes: ThemeMode[] = ['system', 'light', 'dark']
  const current = modes.indexOf(appStore.themeMode)
  const next = modes[(current + 1) % modes.length]
  appStore.setTheme(next)
}

const themeIcon: Record<string, string> = {
  system: 'M12 3v2m0 14v2M5.6 5.6l1.4 1.4m10 10l1.4 1.4M3 12h2m14 0h2M5.6 18.4l1.4-1.4m10-10l1.4-1.4',
  light: 'M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10zM12 1v3m0 16v3m11-11h-3M4 12H1m17.5-6.5l-2 2m-9 9l-2 2m13 0l-2-2m-9-9l-2-2',
  dark: 'M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z'
}

const themeLabel: Record<string, string> = {
  system: '跟随系统',
  light: '亮色',
  dark: '暗色'
}
</script>

<template>
  <aside class="desktop-sidebar">
    <!-- 品牌区 -->
    <div class="sidebar-brand">
      <div class="sidebar-brand-icon">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M4 4h16v4H4V4zm0 6h16v4H4v-4zm0 6h10v4H4v-4z" fill="currentColor" opacity="0.9"/>
        </svg>
      </div>
      <span class="sidebar-brand-text">箓川码笺</span>
    </div>

    <!-- 导航菜单 -->
    <nav class="sidebar-nav">
      <router-link
        v-for="r in navRoutes"
        :key="r.path"
        class="sidebar-nav-item"
        :class="{ active: isActive(r.path) }"
        :to="r.path"
        :title="r.title"
        :aria-label="r.title"
      >
        <span class="sidebar-nav-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path :d="icons[r.icon]" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </span>
        <span class="sidebar-nav-label">{{ r.title }}</span>
      </router-link>
    </nav>

    <!-- 底部：主题切换 + 后端状态 -->
    <div class="sidebar-footer">
      <a class="sidebar-footer-item" @click="cycleTheme" :title="themeLabel[appStore.themeMode]">
        <span class="sidebar-nav-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path :d="themeIcon[appStore.themeMode]" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </span>
        <span class="sidebar-nav-label">{{ themeLabel[appStore.themeMode] }}</span>
      </a>
      <a class="sidebar-footer-item" :title="appStore.backendReady ? '后端已连接' : '后端未连接'">
        <span class="sidebar-nav-icon">
          <span
            :style="{
              display: 'inline-block',
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: appStore.backendReady ? 'var(--status-success)' : 'var(--status-error)'
            }"
          />
        </span>
        <span class="sidebar-nav-label">{{ appStore.backendReady ? '已连接' : '未连接' }}</span>
      </a>
    </div>
  </aside>
</template>
