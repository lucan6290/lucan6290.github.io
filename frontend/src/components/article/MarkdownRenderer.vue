<template>
  <div class="md-viewer" @click="navigate">
    <Viewer v-if="pluginsReady" :value="content" :plugins="plugins" />
    <div v-else class="loading">渲染器加载中…</div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import type { BytemdPlugin } from 'bytemd';
import { contentPath, resolveContentUrl } from '@/composables/contentPaths';
import { useContent } from '@/composables/useContent';
import { Viewer } from '@bytemd/vue-next';
import gfm from '@bytemd/plugin-gfm';
import highlight from '@bytemd/plugin-highlight';
import math from '@bytemd/plugin-math';
import mermaid from '@bytemd/plugin-mermaid';
import breaks from '@bytemd/plugin-breaks';

import 'bytemd/dist/index.css';
import 'highlight.js/styles/github.css';
import 'katex/dist/katex.css';

const props = defineProps<{ content: string; relativePath: string; title?: string }>();
const router = useRouter();
const { findNodeByPath, getArticle } = useContent();

const resourceModules = import.meta.glob<string>('/content/**/*.{png,PNG,jpg,JPG,jpeg,JPEG,gif,GIF,svg,SVG,webp,WEBP,avif,AVIF,bmp,BMP,ico,ICO,pdf,PDF}', {
  query: '?url', import: 'default', eager: true,
});
const resources = Object.fromEntries(Object.entries(resourceModules).map(([key, url]) => [key.slice('/content/'.length), url]));

type MarkdownNode = { type: string; url?: string; value?: string; depth?: number; children?: MarkdownNode[] };
const contentLinks = computed<BytemdPlugin>(() => ({
  remark: (processor) => processor.use(() => (tree: MarkdownNode) => {
    const first = tree.children?.[0];
    const text = (node: MarkdownNode): string => node.value || node.children?.map(text).join('') || '';
    if (props.title && first?.type === 'heading' && first.depth === 1 && text(first) === props.title) {
      tree.children!.shift();
    }
    const visit = (node: MarkdownNode) => {
      if (node.url && ['image', 'link', 'definition'].includes(node.type)) {
        node.url = resolveContentUrl(node.url, props.relativePath, resources);
      }
      node.children?.forEach(visit);
    };
    visit(tree);
  }),
  viewerEffect({ markdownBody }) {
    const used = new Set<string>();
    markdownBody.querySelectorAll<HTMLElement>('h1, h2, h3, h4, h5, h6').forEach((heading) => {
      const base = (heading.textContent || '').trim().toLowerCase().replace(/[^\p{L}\p{N}\p{M}\s_-]/gu, '').replace(/\s/g, '-') || 'section';
      let id = base;
      let index = 1;
      while (used.has(id)) id = `${base}-${index++}`;
      used.add(id);
      heading.id = id;
    });
    const frame = requestAnimationFrame(() => {
      if (!location.hash) return;
      let id: string;
      try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
      const target = document.getElementById(id);
      if (target && markdownBody.contains(target)) {
        window.scrollTo({ top: target.getBoundingClientRect().top + window.scrollY - 80 });
      }
    });
    return () => cancelAnimationFrame(frame);
  },
}));

function navigate(event: MouseEvent) {
  if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
  const anchor = (event.target as Element).closest<HTMLAnchorElement>('a[href]');
  if (!anchor || anchor.target || anchor.hasAttribute('download')) return;
  const url = new URL(anchor.href);
  if (url.origin !== location.origin) return;
  const target = router.resolve(url.pathname + url.search + url.hash);
  if (target.name !== 'content') return;
  const path = contentPath('/' + String(target.params.section), target.params.pathMatch);
  if (!getArticle(path) && !findNodeByPath(path)) return;
  event.preventDefault();
  void router.push(url.pathname + url.search + url.hash);
}

const pluginsReady = ref(false);
const plugins = computed(() => [gfm(), highlight(), math(), mermaid(), breaks(), contentLinks.value]);

onMounted(() => {
  pluginsReady.value = true;
});
</script>

<style>
/* ByteMD viewer 全局样式覆写，与 site/ 正文风格对齐 */
.md-viewer .bytemd-viewer {
  font-family: var(--ifm-font-family-base);
  font-size: 18px;
  line-height: 1.9;
  color: var(--site-text);
}
.md-viewer .bytemd-viewer h1 { font-size: 46px; line-height: 1.16; }
.md-viewer .bytemd-viewer h2 {
  margin-top: 46px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--site-border);
}
.md-viewer .bytemd-viewer p,
.md-viewer .bytemd-viewer li { color: var(--site-text); }
.md-viewer .bytemd-viewer img {
  display: block;
  margin: 20px auto;
  max-width: 80%;
  max-height: 560px;
  border-radius: 8px;
  box-shadow: 0 2px 12px var(--site-shadow);
}
.md-viewer .bytemd-viewer pre {
  background: var(--site-surface);
  border: 1px solid var(--site-border);
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
}
.md-viewer .bytemd-viewer code {
  font-family: var(--ifm-font-family-monospace);
  font-size: 0.92em;
}
.md-viewer .bytemd-viewer blockquote {
  border-left: 4px solid var(--site-border);
  padding: 8px 16px;
  color: var(--site-text-muted);
  background: var(--site-accent-soft);
  border-radius: 0 8px 8px 0;
}
.md-viewer .bytemd-viewer table { width: 100%; border-collapse: collapse; margin: 20px 0; }
.md-viewer .bytemd-viewer th,
.md-viewer .bytemd-viewer td { border: 1px solid var(--site-border); padding: 10px 14px; text-align: left; }
.md-viewer .bytemd-viewer tr:nth-child(2n) { background: var(--site-accent-soft); }
</style>
