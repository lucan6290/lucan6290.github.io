<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NConfigProvider,
  NMessageProvider,
  NDialogProvider,
  NLayout,
  NMenu,
  NIcon,
  NButton,
  type MenuOption
} from 'naive-ui'
import { useAuthStore } from '@/stores/auth'
import { useModeStore } from '@/stores/mode'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const modeStore = useModeStore()

// 仅非登录页显示导航
const showNav = computed(() => route.path !== '/login')

// 当前选中菜单
const currentKey = computed(() => route.path)

// 菜单选项
const menuOptions: MenuOption[] = [
  {
    label: '仪表盘',
    key: '/',
  },
  {
    label: '文章管理',
    key: '/posts',
  },
  {
    label: '编辑器',
    key: '/editor',
  },
  {
    label: '图片管理',
    key: '/media',
  },
  {
    label: '设置',
    key: '/settings',
  },
]

function handleMenuClick(key: string) {
  router.push(key)
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function backToBlog() {
  window.location.href = '/'
}
</script>

<template>
  <n-config-provider>
    <n-message-provider>
      <n-dialog-provider>
        <!-- 登录页不显示侧边栏 -->
        <template v-if="!showNav">
          <router-view />
        </template>

        <!-- 有侧边栏布局 -->
        <n-layout v-else has-sider style="height: 100vh">
          <n-layout-sider
            bordered
            collapse-mode="width"
            :collapsed-width="64"
            :width="160"
            :collapsed="false"
          >
            <div class="sider-header">
              <n-button text strong @click="router.push('/')" style="font-size: 16px">
                箓川码笺
              </n-button>
            </div>

            <n-menu
              :value="currentKey"
              :options="menuOptions"
              @update:value="handleMenuClick"
            />

            <div class="sider-footer">
              <n-button
                size="small"
                type="primary"
                ghost
                block
                @click="backToBlog"
              >
                返回博客
              </n-button>
              <n-button
                v-if="modeStore.isOnline"
                size="small"
                type="error"
                ghost
                block
                style="margin-top: 8px"
                @click="handleLogout"
              >
                退出登录
              </n-button>
            </div>
          </n-layout-sider>

          <n-layout content-style="overflow: auto;">
            <router-view />
          </n-layout>
        </n-layout>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<style>
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>

<style scoped>
.sider-header {
  padding: 16px;
  text-align: center;
  border-bottom: 1px solid #e8e8e8;
}

.sider-footer {
  position: absolute;
  bottom: 16px;
  left: 0;
  right: 0;
  padding: 0 16px;
  text-align: center;
}
</style>
