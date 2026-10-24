<template>
  <div v-if="headings.length" class="toc-action-bar">
    <button
      ref="trigger"
      class="toc-trigger"
      type="button"
      aria-label="本文目录"
      aria-controls="article-toc-panel"
      :aria-expanded="visible"
      @click="toggle"
    >本文目录</button>
  </div>
  <nav
    v-if="headings.length"
    v-show="visible"
    id="article-toc-panel"
    ref="panel"
    class="custom-toc-float"
    aria-label="本文目录"
  >
    <div class="toc-header">
      <span class="toc-header__title">目录</span>
      <button class="toc-header__btn" type="button" aria-label="关闭本文目录" @click="hide(true)">✕</button>
    </div>
    <ul class="table-of-contents">
      <li v-for="h in headings" :key="h.id" class="toc-tree-item" :class="`toc-tree-item--level-${h.level}`">
        <a
          class="table-of-contents__link"
          :class="{ 'table-of-contents__link--active': activeId === h.id }"
          :aria-current="activeId === h.id ? 'location' : undefined"
          :href="`#${h.id}`"
          @click.prevent="scrollTo(h.id)"
        >{{ h.text }}</a>
      </li>
    </ul>
  </nav>
</template>

<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';

type Heading = { id: string; text: string; level: number };

const visible = ref(false);
const activeId = ref('');
const headings = ref<Heading[]>([]);
const trigger = ref<HTMLButtonElement | null>(null);
const panel = ref<HTMLElement | null>(null);
const route = useRoute();
let collectTimer: number | null = null;
let observer: IntersectionObserver | null = null;

async function show() {
  visible.value = true;
  await nextTick();
  panel.value?.querySelector<HTMLAnchorElement>('a')?.focus();
}
function hide(restoreFocus = false) {
  visible.value = false;
  if (restoreFocus) trigger.value?.focus();
}
function toggle() { if (visible.value) hide(true); else void show(); }
function onKeydown(event: KeyboardEvent) { if (event.key === 'Escape' && visible.value) hide(true); }
function onPointerdown(event: PointerEvent) {
  const target = event.target as Node;
  if (visible.value && !panel.value?.contains(target) && !trigger.value?.contains(target)) hide();
}

function collectHeadings() {
  const nodes = document.querySelectorAll('.md-viewer h2, .md-viewer h3');
  const list: Heading[] = [];
  nodes.forEach((n) => {
    const el = n as HTMLElement;
    if (!el.id) el.id = encodeURIComponent(el.textContent?.trim() || '').replace(/%/g, '-').slice(0, 80);
    list.push({ id: el.id, text: el.textContent?.trim() || '', level: el.tagName === 'H2' ? 0 : 1 });
  });
  headings.value = list;
}

function scrollTo(id: string) {
  const el = document.getElementById(id);
  if (el) {
    const y = el.getBoundingClientRect().top + window.scrollY - 80;
    window.scrollTo({ top: y, behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    activeId.value = id;
    if (!el.hasAttribute('tabindex')) {
      el.tabIndex = -1;
      el.addEventListener('blur', () => el.removeAttribute('tabindex'), { once: true });
    }
    el.focus({ preventScroll: true });
    hide();
  }
}

function setupObserver() {
  observer?.disconnect();
  observer = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (e.isIntersecting) { activeId.value = e.target.id; break; }
      }
    },
    { rootMargin: '-80px 0px -70% 0px', threshold: 0 },
  );
  headings.value.forEach((h) => {
    const el = document.getElementById(h.id);
    if (el) observer!.observe(el);
  });
}

function scheduleCollect() {
  if (collectTimer !== null) window.clearTimeout(collectTimer);
  observer?.disconnect();
  headings.value = [];
  activeId.value = '';
  hide();
  // 等 Markdown 渲染器更新章节节点。
  collectTimer = window.setTimeout(() => { collectHeadings(); setupObserver(); collectTimer = null; }, 300);
}

onMounted(() => {
  scheduleCollect();
  window.addEventListener('keydown', onKeydown);
  window.addEventListener('pointerdown', onPointerdown);
});
watch(() => route.fullPath, scheduleCollect);
onUnmounted(() => {
  observer?.disconnect();
  if (collectTimer !== null) window.clearTimeout(collectTimer);
  window.removeEventListener('keydown', onKeydown);
  window.removeEventListener('pointerdown', onPointerdown);
});
</script>

<style scoped>
.toc-action-bar {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 200;
}
.toc-trigger {
  min-height: 44px;
  padding: 0 16px;
  border-radius: 8px;
  background: var(--site-accent);
  color: var(--site-on-accent);
  font-size: .88rem;
  font-weight: 650;
  box-shadow: 0 4px 14px var(--site-shadow);
}
.toc-trigger:hover { background: var(--site-accent-hover); }
.custom-toc-float {
  position: fixed;
  right: 16px;
  bottom: 76px;
  width: min(320px, calc(100vw - 32px));
  max-height: 70vh;
  padding: 16px;
  background: var(--site-background);
  border: 1px solid var(--site-border);
  border-radius: 8px;
  box-shadow: 0 12px 32px var(--site-shadow);
  z-index: 201;
  overflow-y: auto;
}
.toc-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; position: sticky; top: 0; background: var(--site-background); z-index: 2; padding-bottom: 8px; }
.toc-header__title { font-size: 1.1rem; font-weight: 700; color: var(--site-text); }
.toc-header__btn { width: 44px; height: 44px; border-radius: 8px; background: var(--site-accent-soft); color: var(--site-text-muted); display: grid; place-items: center; transition: background 180ms, color 180ms; }
.toc-header__btn:hover { background: var(--site-border); color: var(--ifm-color-primary); }

.table-of-contents { list-style: none; padding: 0; margin: 0; position: relative; }
.table-of-contents::after { content: ''; position: absolute; top: 2px; bottom: 2px; left: 5px; width: 2px; border-radius: 1px; background: var(--site-border); }
.toc-tree-item { padding: 2px 0; }
.table-of-contents__link {
  display: block; padding: 3px 0 3px 18px; color: var(--site-text-secondary); font-size: 15px; line-height: 1.7; word-break: break-word; text-decoration: none; transition: color 150ms;
}
.toc-tree-item--level-1 .table-of-contents__link { font-size: 14px; color: var(--site-text-muted); padding-left: 32px; }
.table-of-contents__link:hover { color: var(--ifm-color-primary); }
.table-of-contents__link--active { color: var(--ifm-color-primary) !important; font-weight: 600; }
@media (prefers-reduced-motion: reduce) {
  .toc-header__btn, .table-of-contents__link { transition: none; }
}
@media (max-width: 996px) {
  .toc-action-bar {
    right: 0;
    bottom: 0;
    left: 0;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    min-height: 64px;
    padding: 0 20px;
    border-top: 1px solid var(--site-border);
    background: var(--site-background);
  }
  .toc-trigger { box-shadow: none; }
}
</style>
