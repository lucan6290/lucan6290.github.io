<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAppStore } from '@/stores/app'
import { api } from '@/api/index'
import { setAuthSession, isAuthenticated } from '@/utils/auth'
import WindowTitlebar from '@/components/WindowTitlebar.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import ToastContainer from '@/components/ToastContainer.vue'

const appStore = useAppStore()
const backendStarting = ref(true)
const authReady = ref(false)

async function ensureAuthenticated() {
  try {
    if (isAuthenticated()) return
    const username = window.__ADMIN_USERNAME__ || import.meta.env.VITE_ADMIN_USERNAME || 'admin'
    const password = window.__ADMIN_PASSWORD__ || import.meta.env.VITE_ADMIN_PASSWORD || 'admin123'
    const result = await api.loginAdmin(username, password) as {
      access_token: string
      expires_at: number
      username: string
    }
    setAuthSession(result.access_token, result.expires_at, result.username)
  } catch {
    appStore.showToast('自动登录失败，请检查后端配置', 'error', 5000)
  } finally {
    // 无论登录成功与否都渲染页面，避免一直卡在启动遮罩
    authReady.value = true
  }
}

async function waitBackendAndAuth() {
  const ok = await appStore.checkBackendHealth()
  if (ok) {
    await ensureAuthenticated()
  } else {
    appStore.showToast('后端服务启动失败，请检查环境配置', 'error', 5000)
    authReady.value = true
  }
}

onMounted(async () => {
  appStore.init()
  // 等待 Tauri 注入后端端口
  let attempts = 0
  const waitForBackend = setInterval(async () => {
    attempts++
    if (typeof window !== 'undefined' && window.__BACKEND_PORT__) {
      clearInterval(waitForBackend)
      backendStarting.value = false
      await waitBackendAndAuth()
    } else if (attempts > 60) {
      // 6 秒超时（开发模式回退）
      clearInterval(waitForBackend)
      backendStarting.value = false
      await waitBackendAndAuth()
    }
  }, 100)
})
</script>

<template>
  <div class="desktop-shell" :class="{ 'sidebar-collapsed': appStore.sidebarCollapsed }">
    <WindowTitlebar />
    <AppSidebar />
    <main class="desktop-main">
      <router-view v-if="authReady" v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <ToastContainer />
    <!-- 后端启动中遮罩 -->
    <div v-if="backendStarting" class="loading-overlay">
      <div class="spinner" style="width: 28px; height: 28px;"></div>
      <div class="loading-overlay-text">正在启动后端服务...</div>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 120ms ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
