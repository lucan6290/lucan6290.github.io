import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useModeStore } from '@/stores/mode'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: {
      requiresAuth: false
    }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/posts',
    name: 'Posts',
    component: () => import('@/views/Posts.vue'),
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/editor',
    name: 'Editor',
    component: () => import('@/views/Editor.vue'),
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/media',
    name: 'Media',
    component: () => import('@/views/Media.vue'),
    meta: {
      requiresAuth: true
    }
  }
]

const router = createRouter({
  history: createWebHistory('/admin/'),
  routes
})

// 全局前置守卫
router.beforeEach(async (to) => {
  const authStore = useAuthStore()
  const modeStore = useModeStore()

  // 如果目标路由需要认证
  if (to.meta.requiresAuth) {
    // 本地模式：跳过认证，直接放行
    if (modeStore.isLocal) {
      return true
    }

    // 在线模式：检查 GitHub 认证
    if (!authStore.isAuthenticated) {
      // 尝试检查现有 token
      const isValid = await authStore.checkAuth()
      if (!isValid) {
        // 未认证，跳转到登录页
        return {
          path: '/login',
          query: { redirect: to.fullPath }
        }
      }
    }
  }

  // 如果已登录用户访问登录页，重定向到首页
  if (to.path === '/login' && authStore.isAuthenticated && modeStore.isOnline) {
    return '/'
  }

  return true
})

export default router