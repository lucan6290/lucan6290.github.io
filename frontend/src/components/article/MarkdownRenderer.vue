<template>
  <div class="md-viewer">
    <Viewer v-if="pluginsReady" :value="content" :plugins="plugins" />
    <div v-else class="loading">渲染器加载中…</div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, shallowRef } from 'vue';
import { Viewer } from '@bytemd/vue-next';
import gfm from '@bytemd/plugin-gfm';
import highlight from '@bytemd/plugin-highlight';
import math from '@bytemd/plugin-math';
import mermaid from '@bytemd/plugin-mermaid';
import breaks from '@bytemd/plugin-breaks';

import 'bytemd/dist/index.css';
import 'highlight.js/styles/github.css';
import 'katex/dist/katex.css';

defineProps<{ content: string }>();

const pluginsReady = ref(false);
const plugins = shallowRef<any[]>([]);

onMounted(() => {
  plugins.value = [gfm(), highlight(), math(), mermaid(), breaks()];
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
