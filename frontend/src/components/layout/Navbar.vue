<template>
  <header class="navbar">
    <div class="navbar__inner">
      <router-link class="navbar__brand" to="/">
        <span class="navbar__title">箓川码笺</span>
      </router-link>

      <nav id="section-navigation" class="navbar__items navbar__items--left" :class="{ 'navbar__items--open': mobileOpen }" aria-label="顶部栏目">
        <div
          v-for="entry in navEntries"
          :key="entry.key"
          class="navbar__item dropdown"
          @mouseenter="open(entry.key)"
          @mouseleave="close(entry.key)"
          @focusin="open(entry.key)"
          @focusout="close(entry.key)"
        >
          <button class="navbar__link" type="button" aria-haspopup="true" :aria-expanded="active === entry.key" @click="open(entry.key)" @keydown.esc="active = null">
            {{ entry.label }}
            <span class="caret" aria-hidden="true" />
          </button>
          <ul v-show="active === entry.key" class="dropdown__menu">
            <li v-for="it in entry.items" :key="it.to">
              <router-link class="dropdown__link" :to="it.to">{{ it.label }}</router-link>
            </li>
          </ul>
        </div>

      </nav>

      <div class="navbar__items navbar__items--right">
        <button class="navbar__link mobile-nav-toggle" type="button" aria-controls="section-navigation" :aria-expanded="mobileOpen" @click="mobileOpen = !mobileOpen">栏目</button>
        <button class="theme-toggle" type="button" title="切换主题" @click="toggle">
          <span v-if="theme === 'light'" aria-hidden="true">🌙</span>
          <span v-else aria-hidden="true">☀️</span>
        </button>
        <a class="navbar__link" href="https://github.com/lucan6290" target="_blank" rel="noopener">GitHub</a>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { createNavEntries } from '@/config/nav';
import { useContent } from '@/composables/useContent';
import { useTheme } from '@/composables/useTheme';

const { theme, toggle } = useTheme();
const { manifest } = useContent();
const navEntries = computed(() => createNavEntries(manifest.value.tree));
const mobileOpen = ref(false);
const route = useRoute();
const active = ref<string | null>(null);
watch(() => route.fullPath, () => { mobileOpen.value = false; active.value = null; });
let timer: number | null = null;

function open(key: string) {
  if (timer) { clearTimeout(timer); timer = null; }
  active.value = key;
}
function close(key: string) {
  if (active.value !== key) return;
  timer = window.setTimeout(() => {
    if (active.value === key) active.value = null;
  }, 120);
}
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: var(--ifm-navbar-height);
  background: var(--site-background);
  border-bottom: 1px solid var(--site-border);
  z-index: 1000;
}
.navbar__inner {
  max-width: 1440px;
  margin: 0 auto;
  height: 100%;
  padding: 0 24px;
  display: flex;
  align-items: center;
  gap: 32px;
}
.navbar__brand { text-decoration: none; color: inherit; }
.navbar__title { font-size: 1.02rem; font-weight: 800; color: var(--site-text); }
.navbar__items { display: flex; align-items: center; gap: 6px; }
.navbar__items--left { flex: 1; }
.navbar__items--right { gap: 12px; }

.navbar__link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  color: var(--site-text-secondary);
  font-weight: 500;
  font-size: 0.92rem;
  border-radius: 6px;
  transition: color 180ms, background 180ms;
  cursor: pointer;
  background: transparent;
}
.navbar__link:hover { color: var(--ifm-color-primary); background: var(--site-accent-soft); }

.caret {
  display: inline-block;
  width: 0; height: 0;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-top: 5px solid currentColor;
  opacity: 0.6;
  margin-left: 2px;
}

.dropdown { position: relative; }
.dropdown__menu {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  min-width: 188px;
  padding: 8px;
  list-style: none;
  background: var(--site-surface);
  border: 1px solid var(--site-border);
  border-radius: 8px;
  box-shadow: 0 18px 42px var(--site-shadow);
  z-index: 1001;
}
.dropdown__link {
  display: block;
  padding: 8px 12px;
  border-radius: 6px;
  color: var(--site-text-secondary);
  font-weight: 500;
  line-height: 1.35;
}
.dropdown__link:hover,
.dropdown__link.router-link-active {
  background: var(--site-accent-soft);
  color: var(--ifm-color-primary-dark);
  font-weight: 600;
}

.theme-toggle {
  width: 32px; height: 32px;
  border-radius: 8px;
  display: grid; place-items: center;
  font-size: 1rem;
  background: var(--site-accent-soft);
  color: var(--site-text);
  transition: background 180ms;
}
.theme-toggle:hover { background: var(--site-border); }

.mobile-nav-toggle { display: none; }

@media (max-width: 996px) {
  .navbar__items--left { display: none; }
  .navbar__inner { gap: 12px; padding: 0 12px; }
  .navbar__items--right { margin-left: auto; gap: 4px; }
  .navbar__items--right > a { display: none; }
  .mobile-nav-toggle { display: inline-flex; }
  .navbar__items--left.navbar__items--open {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    position: fixed;
    top: var(--ifm-navbar-height);
    left: 0;
    right: 0;
    max-height: calc(100vh - var(--ifm-navbar-height));
    overflow-y: auto;
    padding: 12px;
    background: var(--site-surface);
    border-bottom: 1px solid var(--site-border);
  }
  .dropdown__menu { position: static; box-shadow: none; margin: 0 8px 8px; }
}
</style>
