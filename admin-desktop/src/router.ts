import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '仪表盘', icon: 'dashboard' }
  },
  {
    path: '/posts',
    name: 'Posts',
    component: () => import('@/views/Posts.vue'),
    meta: { title: '文档管理', icon: 'posts' }
  },
  {
    path: '/editor',
    name: 'Editor',
    component: () => import('@/views/Editor.vue'),
    meta: { title: '编辑器', icon: 'editor' }
  },
  {
    path: '/media',
    name: 'Media',
    component: () => import('@/views/Unavailable.vue'),
    meta: { title: '媒体库', icon: 'media' }
  },
  {
    path: '/ai-writing',
    name: 'AIWriting',
    component: () => import('@/views/Unavailable.vue'),
    meta: { title: 'AI 写作', icon: 'ai' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '设置', icon: 'settings' }
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 更新页面标题
router.afterEach((to, _from, failure) => {
  if (failure) return
  const title = to.meta.title as string
  if (title) {
    document.title = `箓川码笺管理端 — ${title}`
  }
})

export default router
