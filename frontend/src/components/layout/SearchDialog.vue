<template>
  <Teleport to="body">
    <dialog ref="dialog" class="search-dialog" aria-labelledby="search-heading" @cancel.prevent="close" @keydown.esc.prevent.stop="close" @click="onBackdropClick">
      <section class="search-panel">
        <header class="search-header">
          <h2 id="search-heading">搜索文章</h2>
          <button class="search-close" type="button" aria-label="关闭搜索" @click="close">关闭 <kbd>Esc</kbd></button>
        </header>
        <label class="search-label" for="reader-search">搜索标题、标签或正文</label>
        <input
          id="reader-search"
          ref="input"
          v-model="query"
          class="search-input"
          type="search"
          placeholder="输入中文或英文关键词…"
          autocomplete="off"
          spellcheck="false"
          aria-describedby="search-status"
        />
        <p id="search-status" class="search-status" role="status" aria-live="polite">
          <template v-if="loading">正在加载搜索索引…</template>
          <template v-else-if="error">搜索加载失败，请检查网络后重试。</template>
          <template v-else-if="!query.trim()">搜索全站文章，多个关键词可用空格分隔。</template>
          <template v-else-if="!results.length">没有找到相关文章，试试其他关键词。</template>
          <template v-else>找到 {{ results.length === 30 ? '至少 30' : results.length }} 篇文章{{ results.length === 30 ? '，显示前 30 篇' : '' }}。</template>
        </p>
        <button v-if="error" class="search-retry" type="button" @click="load">重新加载</button>
        <ul v-if="results.length" class="search-results" aria-label="搜索结果">
          <li v-for="result in results" :key="result.id">
            <router-link class="search-result" :to="contentHref(result.path)" @click="close">
              <span class="search-result__path">{{ locationLabel(result.path) }}</span>
              <span class="search-result__title">{{ result.title }}</span>
              <span v-if="result.description" class="search-result__description">{{ result.description }}</span>
            </router-link>
          </li>
        </ul>
        <footer class="search-footer">Tab 选择结果 · Enter 打开文章 · Esc 关闭</footer>
      </section>
    </dialog>
  </Teleport>
</template>

<script lang="ts">
import type { SearchResult } from '@/composables/search';

type Search = (query: string) => SearchResult[];
let searchPromise: Promise<Search> | null = null;

function loadSearch(): Promise<Search> {
  searchPromise ??= Promise.all([
    import('@/composables/search'),
    import('@/generated/search-index.json'),
  ]).then(([{ createSearch }, { default: documents }]) => createSearch(documents)).catch((error) => {
    searchPromise = null;
    throw error;
  });
  return searchPromise;
}
</script>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, shallowRef } from 'vue';
import { contentHref } from '@/composables/contentPaths';
import { sectionLabel } from '@/config/nav';

const emit = defineEmits<{ close: [] }>();
const dialog = ref<HTMLDialogElement | null>(null);
const input = ref<HTMLInputElement | null>(null);
const query = ref('');
const search = shallowRef<Search | null>(null);
const loading = ref(true);
const error = ref(false);
const results = computed(() => search.value?.(query.value) ?? []);
let previousOverflow = '';

function close() {
  dialog.value?.close();
  emit('close');
}

function onBackdropClick(event: MouseEvent) {
  if (event.target === dialog.value) close();
}

function locationLabel(path: string) {
  const [section, ...folders] = path.slice(1).split('/');
  folders.pop();
  return [sectionLabel(section), ...folders.map(folder => folder.replace(/^\d+[-_]/, ''))].join(' / ');
}

async function load() {
  loading.value = true;
  error.value = false;
  try {
    search.value = await loadSearch();
  } catch {
    error.value = true;
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  previousOverflow = document.body.style.overflow;
  document.body.style.overflow = 'hidden';
  dialog.value?.showModal();
  input.value?.focus();
  void load();
});

onUnmounted(() => {
  dialog.value?.close();
  document.body.style.overflow = previousOverflow;
});
</script>

<style scoped>
.search-dialog {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100dvh;
  max-width: none;
  max-height: none;
  margin: 0;
  padding: 10vh 20px 24px;
  border: 0;
  background: transparent;
  color: var(--site-text);
  overflow-y: auto;
}
.search-dialog::backdrop { background: rgb(12 27 51 / 55%); }
.search-panel {
  display: flex;
  flex-direction: column;
  width: min(100%, 680px);
  max-height: 76dvh;
  margin: 0 auto;
  padding: 24px;
  border: 1px solid var(--site-border);
  border-radius: 14px;
  background: var(--site-surface);
  box-shadow: 0 24px 70px var(--site-shadow);
}
.search-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.search-header h2 { font-size: 1.15rem; }
.search-close { min-height: 44px; padding: 6px 8px; border-radius: 7px; color: var(--site-text-secondary); }
kbd { margin-left: 5px; padding: 1px 5px; border: 1px solid var(--site-border); border-radius: 4px; font-size: 0.72rem; }
.search-label { margin: 12px 0 8px; color: var(--site-text-secondary); font-size: 0.85rem; }
.search-input {
  flex-shrink: 0;
  width: 100%;
  min-height: 48px;
  padding: 10px 14px;
  border: 1px solid var(--site-border);
  border-radius: 8px;
  background: var(--site-background);
  color: var(--site-text);
  font: inherit;
}
.search-input::placeholder { color: var(--site-text-muted); }
.search-status { flex-shrink: 0; padding: 14px 0; color: var(--site-text-muted); font-size: 0.85rem; }
.search-retry { align-self: flex-start; min-height: 44px; padding: 8px 14px; border-radius: 7px; background: var(--site-accent-soft); color: var(--ifm-color-primary); }
.search-results { min-height: 0; overflow-y: auto; padding: 4px; margin: 0 -4px; list-style: none; }
.search-results li + li { border-top: 1px solid var(--site-border); }
.search-result { display: flex; flex-direction: column; gap: 3px; padding: 14px 12px; border-radius: 7px; overflow-wrap: anywhere; }
.search-result:hover, .search-result:focus-visible, .search-close:hover { background: var(--site-accent-soft); }
.search-result__path { font-size: 0.72rem; color: var(--site-text-muted); }
.search-result__title { font-size: 1rem; font-weight: 650; color: var(--ifm-color-primary); }
.search-result__description { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; font-size: 0.83rem; color: var(--site-text-secondary); }
.search-footer { flex-shrink: 0; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--site-border); color: var(--site-text-muted); font-size: 0.75rem; }
@media (max-width: 600px) {
  .search-dialog { padding: 16px 12px; }
  .search-panel { max-height: calc(100dvh - 32px); padding: 16px; border-radius: 10px; }
  .search-close kbd { display: none; }
}
</style>
