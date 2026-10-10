<template>
  <main class="page-shell">
    <section class="simple-page">
      <p class="eyebrow">Archive</p>
      <h1>归档</h1>
      <div v-if="years.length" class="archive-tree">
        <section v-for="y in years" :key="y" class="year-group">
          <h2>{{ y }}</h2>
          <div v-for="m in monthsOf(y)" :key="m" class="month-group">
            <h3>{{ y }}-{{ m }}</h3>
            <ul>
              <li v-for="path in archive[y][m]" :key="path">
                <router-link :to="path">{{ titleOf(path) }}</router-link>
              </li>
            </ul>
          </div>
        </section>
      </div>
      <p v-else class="empty">暂无归档。</p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useContent } from '@/composables/useContent';

const { getArchive, manifest } = useContent();
const archive = computed(() => getArchive());
const years = computed(() => Object.keys(archive.value).sort((a, b) => Number(b) - Number(a)));
function monthsOf(y: string) { return Object.keys(archive.value[y]).sort((a, b) => Number(b) - Number(a)); }
function titleOf(path: string) { return manifest.value?.articles[path]?.frontmatter.title || path; }
</script>

<style scoped>
.page-shell { min-height: calc(100vh - var(--ifm-navbar-height)); padding: 64px 24px 96px; background: var(--site-background); }
.simple-page { width: min(880px, 100%); margin: 0 auto; }
.eyebrow { margin: 0 0 12px; color: var(--ifm-color-primary); font-size: 0.82rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
.simple-page h1 { margin: 0 0 32px; color: var(--site-text); font-size: clamp(2rem, 4vw, 3.2rem); line-height: 1.12; }
.year-group { margin-bottom: 36px; }
.year-group h2 { margin: 0 0 16px; font-size: 1.6rem; color: var(--site-text); border-bottom: 1px solid var(--site-border); padding-bottom: 8px; }
.month-group { margin-bottom: 20px; padding-left: 16px; }
.month-group h3 { margin: 0 0 8px; font-size: 1.05rem; color: var(--site-text-secondary); }
.month-group ul { list-style: none; padding: 0; margin: 0; }
.month-group li { margin-bottom: 6px; }
.month-group a { color: var(--site-text); font-size: 0.95rem; }
.month-group a:hover { color: var(--ifm-color-primary); }
.empty { color: var(--site-text-muted); }
</style>
