import { computed, ref } from 'vue';
import type { ArticleMeta, ContentManifest, TreeNode } from '@/types/content';
import manifestModule from 'virtual:content-manifest';

// 开发和生产均由 Vite 内容插件提供数据，不依赖浏览器顶层 await。
const manifestRef = ref<ContentManifest>(manifestModule);
const ready = ref(true);

export type SortMode = 'prefix' | 'date';

export function useContent() {
  const sortMode = ref<SortMode>('prefix');

  const manifest = computed(() => manifestRef.value);

  function findNodeByPath(path: string): TreeNode | null {
    const m = manifest.value;
    if (!m) return null;
    const target = '/' + path.replace(/^\/+|\/+$/g, '');
    const find = (nodes: TreeNode[]): TreeNode | null => {
      for (const node of nodes) {
        if (node.path === target) return node;
        const child = find(node.children);
        if (child) return child;
      }
      return null;
    };
    return find(m.tree);
  }

  function getArticlesUnder(node: TreeNode | null): ArticleMeta[] {
    if (!node) return [];
    const list: ArticleMeta[] = [];
    const walk = (n: TreeNode) => {
      if (n.article) list.push(n.article);
      n.children.forEach(walk);
    };
    walk(node);
    return applySort(list);
  }

  function applySort(list: ArticleMeta[]): ArticleMeta[] {
    const sticky = list.filter((a) => a.frontmatter.sticky);
    const rest = list.filter((a) => !a.frontmatter.sticky);
    rest.sort((a, b) => {
      if (sortMode.value === 'prefix') {
        if (a.sortKey && b.sortKey) return a.sortKey.localeCompare(b.sortKey);
        if (a.sortKey) return -1;
        if (b.sortKey) return 1;
        return a.frontmatter.title.localeCompare(b.frontmatter.title);
      }
      const da = Date.parse(a.frontmatter.date) || 0;
      const db = Date.parse(b.frontmatter.date) || 0;
      return db - da;
    });
    return [...sticky, ...rest];
  }

  function getArticle(path: string): ArticleMeta | undefined {
    return manifest.value?.articles[path];
  }

  function getPrevNext(path: string) {
    return manifest.value?.prevNext[path] ?? { prev: null, next: null };
  }

  function getAllTags() {
    return manifest.value?.tags ?? {};
  }

  function getArchive() {
    return manifest.value?.archive ?? {};
  }

  function getRecent(limit = 6) {
    const paths = manifest.value?.recent ?? [];
    return paths.slice(0, limit).map((p) => manifest.value!.articles[p]).filter(Boolean);
  }

  function toggleSort() {
    sortMode.value = sortMode.value === 'prefix' ? 'date' : 'prefix';
  }

  return {
    ready,
    manifest,
    sortMode,
    findNodeByPath,
    getArticlesUnder,
    getArticle,
    getPrevNext,
    getAllTags,
    getArchive,
    getRecent,
    toggleSort,
  };
}
