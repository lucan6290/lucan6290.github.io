<template>
  <div class="md-viewer" @click="navigate">
    <Viewer v-if="pluginsReady" :value="renderableContent" :plugins="plugins" />
    <div v-else class="loading">渲染器加载中…</div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import type { BytemdPlugin } from 'bytemd';
import { contentPath } from '@/composables/contentPaths';
import { headingAnchor, resolvePublicMarkdownLink } from '@/utils/publicPaths';
import { useContent } from '@/composables/useContent';
import { transformDocusaurusAdmonitions } from '@/utils/markdownAdmonitions.js';
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
  query: '?url&no-inline', import: 'default', eager: true,
});
const resources = Object.fromEntries(Object.entries(resourceModules).map(([key, url]) => [key.slice('/content/'.length), url]));
const renderableContent = computed(() => transformDocusaurusAdmonitions(props.content));

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
        node.url = resolvePublicMarkdownLink(node.url, props.relativePath, resources, import.meta.env.BASE_URL);
      }
      node.children?.forEach(visit);
    };
    visit(tree);
  }),
  viewerEffect({ markdownBody }) {
    markdownBody.querySelectorAll<HTMLElement>('blockquote').forEach((blockquote) => {
      const title = blockquote.querySelector<HTMLElement>(':scope > p:first-child > strong');
      const marker = title?.textContent?.match(/^\[!(note|tip|info|warning|danger)\]\s*/i);
      if (!title || !marker) return;
      blockquote.classList.add('md-admonition', `md-admonition--${marker[1].toLowerCase()}`);
      title.textContent = (title.textContent || '').slice(marker[0].length);
    });

    const used = new Set<string>();
    markdownBody.querySelectorAll<HTMLElement>('h1, h2, h3, h4, h5, h6').forEach((heading) => {
      const textNode = Array.from(heading.childNodes).find((node) => node.nodeType === Node.TEXT_NODE && node.textContent?.trim());
      const number = textNode?.textContent?.match(/^((?:\d+(?:\.\d+)*[.、)）]|[一二三四五六七八九十]+[、.])\s*)/);
      if (textNode && number) {
        const numberText = number[1].trimEnd();
        const spacing = number[1].slice(numberText.length);
        const badge = document.createElement('span');
        badge.className = 'article-heading-number';
        badge.textContent = numberText;
        textNode.textContent = textNode.textContent!.slice(number[0].length);
        heading.insertBefore(badge, textNode);
        if (spacing) heading.insertBefore(document.createTextNode(spacing), textNode);
      }

      heading.id = headingAnchor(heading.textContent || '', used);
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
  const base = router.options.history.base;
  if (base && url.pathname !== base && !url.pathname.startsWith(base + '/')) return;
  const target = router.resolve((url.pathname.slice(base.length) || '/') + url.search + url.hash);
  if (target.name !== 'content') return;
  const path = contentPath('/' + String(target.params.section), target.params.pathMatch);
  if (!getArticle(path) && !findNodeByPath(path)) return;
  event.preventDefault();
  void router.push(target.fullPath);
}

const pluginsReady = ref(false);
const plugins = computed(() => [gfm(), highlight(), math(), mermaid(), breaks(), contentLinks.value]);

onMounted(() => {
  pluginsReady.value = true;
});
</script>

<style>
/* ByteMD viewer 全局样式覆写，与 site/ 正文风格对齐 */
.md-viewer .markdown-body {
  font-family: var(--ifm-font-family-base);
  font-size: 17px;
  line-height: 1.82;
  color: var(--site-reading-text);
  overflow-wrap: break-word;
}
.md-viewer .markdown-body h1,
.md-viewer .markdown-body h2,
.md-viewer .markdown-body h3,
.md-viewer .markdown-body h4 { color: var(--site-reading-heading); }
.md-viewer .markdown-body h1 { line-height: 1.35; }
.md-viewer .markdown-body h2 {
  margin: 28px 0 12px;
  padding-bottom: 8px;
  font-size: 1.5rem;
  line-height: 1.4;
  border-bottom: 1px solid var(--site-border);
}
.md-viewer .markdown-body > h2:first-child { margin-top: 22px; }
.md-viewer .markdown-body h3,
.md-viewer .markdown-body h4 { margin: 20px 0 8px; }
.md-viewer .markdown-body h1 { font-size: 1.85rem; }
.md-viewer .markdown-body h3 { margin: 20px 0 8px; font-size: 1.25rem; line-height: 1.45; }
.md-viewer .markdown-body h4 { font-size: 1.1rem; }
.md-viewer .markdown-body h5 { font-size: 1rem; }
.md-viewer .markdown-body h6 { font-size: .92rem; }
.md-viewer .markdown-body .article-heading-number { color: var(--site-text-muted); font-size: .76em; font-weight: 600; }
.md-viewer .markdown-body p,
.md-viewer .markdown-body li,
.md-viewer .markdown-body td { color: var(--site-reading-text); }
.md-viewer .markdown-body li + li { margin-top: 4px; }
.md-viewer .markdown-body img {
  display: block;
  margin: 20px auto;
  max-width: 100%;
  max-height: 560px;
  border-radius: 8px;
  box-shadow: 0 2px 16px var(--site-shadow);
}
.md-viewer .markdown-body pre {
  background: var(--site-surface);
  border: 1px solid var(--site-border);
  border-radius: 7px;
  padding: 12px 16px;
  overflow-x: auto;
  line-height: 1.55;
}
.md-viewer .markdown-body code {
  font-family: var(--ifm-font-family-monospace);
  font-size: 0.92em;
}
.md-viewer .markdown-body pre code { font-size: .85em; line-height: inherit; }
.md-viewer .markdown-body pre code.hljs { overflow: visible; padding: 0; background: transparent; }
html[data-theme='dark'] .md-viewer .markdown-body pre code.hljs { color: var(--site-reading-text); }
html[data-theme='dark'] .md-viewer .hljs span { color: inherit; }
html[data-theme='dark'] .md-viewer .markdown-body :is(.hljs-doctag, .hljs-keyword, .hljs-template-tag, .hljs-template-variable, .hljs-type) { color: #ff9b95; }
html[data-theme='dark'] .md-viewer .markdown-body :is(.hljs-title, .hljs-function) { color: #d7b5ff; }
html[data-theme='dark'] .md-viewer .markdown-body :is(.hljs-attr, .hljs-attribute, .hljs-literal, .hljs-meta, .hljs-number, .hljs-operator, .hljs-variable, .hljs-selector-attr, .hljs-selector-class, .hljs-selector-id, .hljs-section) { color: #93caff; }
html[data-theme='dark'] .md-viewer .markdown-body :is(.hljs-string, .hljs-regexp) { color: #b8dcff; }
html[data-theme='dark'] .md-viewer .markdown-body :is(.hljs-built_in, .hljs-symbol) { color: #ffbb7b; }
html[data-theme='dark'] .md-viewer .markdown-body :is(.hljs-comment, .hljs-code, .hljs-formula) { color: #a7b1b9; }
html[data-theme='dark'] .md-viewer .markdown-body :is(.hljs-name, .hljs-quote, .hljs-selector-tag, .hljs-selector-pseudo) { color: #9ce4a5; }
html[data-theme='dark'] .md-viewer .markdown-body .hljs-bullet { color: #e8cd82; }
html[data-theme='dark'] .md-viewer .markdown-body .hljs-addition { color: #aff5b4; background: #033a16; }
html[data-theme='dark'] .md-viewer .markdown-body .hljs-deletion { color: #ffdcd7; background: #67060c; }
.md-viewer .markdown-body :not(pre) > code {
  padding: .12em .34em;
  border-radius: 4px;
  background: var(--site-accent-soft);
  color: var(--ifm-color-primary-dark);
}
.md-viewer .markdown-body blockquote {
  border-left: 3px solid var(--site-accent);
  padding: 8px 17px;
  color: var(--site-reading-text);
  background: var(--site-accent-soft);
  border-radius: 0 5px 5px 0;
}
.md-viewer .markdown-body blockquote.md-admonition { margin: 22px 0; padding: 12px 17px; }
.md-viewer .markdown-body blockquote.md-admonition > p:first-child { margin-bottom: 7px; }
.md-viewer .markdown-body blockquote.md-admonition > p:last-child { margin-bottom: 0; }
.md-viewer .markdown-body blockquote.md-admonition--tip { border-left-color: var(--site-cool); background: var(--site-cool-soft); }
.md-viewer .markdown-body blockquote.md-admonition--warning { border-left-color: var(--site-warm); background: var(--site-warm-soft); }
.md-viewer .markdown-body blockquote.md-admonition--danger { border-left-color: var(--site-danger); background: var(--site-danger-soft); }
.md-viewer .markdown-body table { display: block; width: 100%; overflow-x: auto; border-collapse: collapse; margin: 22px 0; }
.md-viewer .markdown-body th,
.md-viewer .markdown-body td { border: 1px solid var(--site-border); padding: 10px 14px; text-align: left; }
.md-viewer .markdown-body th { border: 1px solid var(--site-border); padding: 10px 14px; text-align: left; background: var(--site-accent-soft); }
.md-viewer .markdown-body tr:nth-child(2n) { background: var(--site-accent-soft); }
@media (max-width: 700px) {
  .md-viewer .markdown-body { font-size: 16px; line-height: 1.8; }
  .md-viewer .markdown-body h2 { margin: 24px 0 10px; font-size: 1.35rem; }
  .md-viewer .markdown-body > h2:first-child { margin-top: 20px; }
  .md-viewer .markdown-body h3 { font-size: 1.15rem; }
  .md-viewer .markdown-body h4 { font-size: 1.05rem; }
  .md-viewer .markdown-body h5 { font-size: .98rem; }
  .md-viewer .markdown-body h6 { font-size: .9rem; }
  .md-viewer .markdown-body pre { padding: 10px 12px; }
}
</style>
