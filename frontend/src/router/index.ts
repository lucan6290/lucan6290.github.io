import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
import manifest from 'virtual:content-manifest';
import { CONTENT_ROUTE_PATH } from '@/composables/contentPaths';
import { hasSeriesRoute, SERIES_ROOT } from '@/utils/seriesPaths';

const hasSection = (name: string) => manifest.tree.some((node) => !node.article && node.name === name);

const routes: RouteRecordRaw[] = [
  { path: '/', name: 'home', component: () => import('@/views/HomePage.vue') },
  { path: '/about', name: 'about', component: () => import('@/views/AboutPage.vue') },
  ...(!hasSection('tags') ? [
    { path: '/tags', name: 'tags', component: () => import('@/views/TagsIndex.vue') },
    { path: '/tags/:tag', name: 'tagged', component: () => import('@/views/TaggedList.vue') },
  ] : []),
  ...(!hasSection('archive') ? [
    { path: '/archive', name: 'archive', component: () => import('@/views/ArchiveView.vue') },
  ] : []),
  ...(hasSeriesRoute(manifest.tree) ? [
    { path: `${SERIES_ROOT}/:id?`, name: 'series', component: () => import('@/views/SeriesView.vue') },
  ] : []),
  { path: CONTENT_ROUTE_PATH, name: 'content', component: () => import('@/views/ContentRoute.vue') },
];

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, _from, saved) {
    if (saved) return saved;
    if (to.hash) {
      let id: string;
      try { id = decodeURIComponent(to.hash.slice(1)); } catch { return { top: 0 }; }
      const el = document.getElementById(id);
      // 首次进入文章时正文可能尚未渲染；渲染器随后完成锚点定位。
      if (el) return { el, top: 80, behavior: 'smooth' };
    }
    return { top: 0 };
  },
});
