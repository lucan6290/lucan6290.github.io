import { computed, ref } from 'vue';
import type { ArticleMeta, ContentManifest, TreeNode } from '@/types/content';

// 构建期由 Vite 插件注入；运行时直接读取静态 JSON 作为兜底
let manifestModule: ContentManifest | null = null;
try {
  // @ts-expect-error virtual module
  manifestModule = (await import('virtual:content-manifest')).default;
} catch {
  manifestModule = null;
}

async function loadManifest(): Promise<ContentManifest> {
  if (manifestModule) return manifestModule;
  const mod = await import('@/generated/content-manifest.json');
  return mod.default as unknown as ContentManifest;
}

const manifestRef = ref<ContentManifest | null>(manifestModule);
const ready = ref(Boolean(manifestModule));

if (!ready.value) {
  loadManifest().then((m) => {
    manifestRef.value = m;
    ready.value = true;
  });
}

export type SortMode = 'prefix' | 'date';

export function useContent() {
  const sortMode = ref<SortMode>('prefix');

  const manifest = computed(() => manifestRef.value);

  function findNodeByPath(path: string): TreeNode | null {
    const m = manifest.value;
    if (!m) return null;
    const segments = path.replace(/^\/+|\/+$/g, '').split('/').filter(Boolean);
    let nodes = m.tree;
    let found: TreeNode | null = null;
    for (const seg of segments) {
      const match = nodes.find((n) => n.name === seg || n.label === seg || n.path === '/' + segments.slice(0, segments.indexOf(seg) + 1).join('/'));
      if (!match) return null;
      found = match;
      nodes = match.children;
    }
    return found;
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
      const da = new Date(a.frontmatter.date).getTime();
      const db = new Date(b.frontmatter.date).getTime();
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
