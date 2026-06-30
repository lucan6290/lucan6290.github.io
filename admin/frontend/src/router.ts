import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
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
    path: '/registry',
    name: 'Registry',
    component: () => import('@/views/Registry.vue'),
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/ai-writing',
    name: 'AIWriting',
    component: () => import('@/views/AIWriting.vue'),
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
  history: createWebHashHistory('/admin/'),
  routes
})

export default router
