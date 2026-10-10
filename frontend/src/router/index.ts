import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  { path: '/', name: 'home', component: () => import('@/views/HomePage.vue') },
  { path: '/projects', name: 'projects', component: () => import('@/views/ProjectsPage.vue') },
  { path: '/about', name: 'about', component: () => import('@/views/AboutPage.vue') },
  { path: '/tags', name: 'tags', component: () => import('@/views/TagsIndex.vue') },
  { path: '/tags/:tag', name: 'tagged', component: () => import('@/views/TaggedList.vue') },
  { path: '/archive', name: 'archive', component: () => import('@/views/ArchiveView.vue') },
  // 知识库 / 博客：统一用 CategoryView + ArticleView，按路径深度区分
  { path: '/knowledge/:pathMatch(.*)*', name: 'knowledge', component: () => import('@/views/ContentRoute.vue') },
  { path: '/blog/:pathMatch(.*)*', name: 'blog', component: () => import('@/views/ContentRoute.vue') },
];

export const router = createRouter({
  history: createWebHistory('/'),
  routes,
  scrollBehavior(to, _from, saved) {
    if (saved) return saved;
    if (to.hash) return { el: to.hash, behavior: 'smooth' };
    return { top: 0 };
  },
});
