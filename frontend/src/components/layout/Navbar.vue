<template>
  <header class="navbar">
    <div class="navbar__inner">
      <!-- Logo + Title -->
      <router-link class="navbar__brand" to="/">
        <img v-if="NAV_LOGO.src" :src="NAV_LOGO.src" :alt="NAV_LOGO.alt" class="navbar__logo" />
        <span class="navbar__title">箓川码笺</span>
      </router-link>

      <!-- Left: dropdown entries -->
      <nav id="section-navigation" class="navbar__items navbar__items--left" :class="{ 'navbar__items--open': mobileOpen }" aria-label="顶部栏目" @keydown.esc="closeMobileMenu">
        <router-link class="navbar__link navbar__home" to="/" @click="mobileOpen = false">首页</router-link>
        <div
          v-for="entry in navEntries"
          :key="entry.key"
          class="navbar__item dropdown"
          @mouseenter="open(entry.key)"
          @mouseleave="close(entry.key)"
          @focusin="open(entry.key)"
          @focusout="close(entry.key)"
        >
          <router-link v-if="!entry.items.length" class="navbar__link" :class="{ 'navbar__link--active': inSection(entry.rootPath) }" :to="entry.rootPath">{{ entry.label }}</router-link>
          <button v-else class="navbar__link" :class="{ 'navbar__link--active': inSection(entry.rootPath) }" type="button" aria-haspopup="true" :aria-expanded="active === entry.key" @click="open(entry.key)" @keydown.esc="active = null">
            {{ entry.label }}
            <span class="caret" aria-hidden="true" />
          </button>
          <ul v-if="entry.items.length" v-show="active === entry.key" class="dropdown__menu">
            <li v-for="it in entry.items" :key="it.to">
              <a v-if="it.external" class="dropdown__link" :href="it.to" target="_blank" rel="noopener">{{ it.label }}</a>
              <router-link v-else class="dropdown__link" :to="it.to">{{ it.label }}</router-link>
            </li>
          </ul>
        </div>
      </nav>

      <!-- Right: GitHub link + theme toggle -->
      <div class="navbar__items navbar__items--right">
        <button ref="searchToggle" class="navbar__link navbar__icon-button search-toggle" type="button" aria-label="搜索" title="搜索" aria-haspopup="dialog" :aria-expanded="searchOpen" @click="openSearch">
          <svg class="navbar__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true" focusable="false">
            <circle cx="10.75" cy="10.75" r="7.25" />
            <path d="m16 16 5 5" />
          </svg>
        </button>
        <button ref="mobileNavToggle" class="navbar__link mobile-nav-toggle" type="button" aria-controls="section-navigation" :aria-expanded="mobileOpen" @click="mobileOpen = !mobileOpen" @keydown.esc="closeMobileMenu">栏目</button>
        <a
          v-for="item in NAV_RIGHT_ITEMS"
          :key="item.href"
          class="navbar__link"
          :class="{ 'navbar__icon-button': item.label === 'GitHub' }"
          :href="item.href"
          :aria-label="item.label"
          :title="item.label"
          target="_blank"
          rel="noopener"
        >
          <svg v-if="item.label === 'GitHub'" class="navbar__icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
            <path d="M12 .297C5.37.297 0 5.67 0 12.297c0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.043-1.61-4.043-1.61-.546-1.387-1.333-1.756-1.333-1.756-1.09-.745.083-.729.083-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.467-1.334-5.467-5.931 0-1.31.469-2.381 1.236-3.221-.123-.303-.536-1.524.117-3.176 0 0 1.008-.322 3.301 1.23a11.52 11.52 0 0 1 3.003-.404c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.655 1.652.243 2.873.12 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.628-5.479 5.921.43.372.823 1.102.823 2.222 0 1.606-.015 2.898-.015 3.293 0 .322.216.694.825.576C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12Z" />
          </svg>
          <template v-else>{{ item.label }}</template>
        </a>
        <button class="navbar__link navbar__icon-button theme-toggle" type="button" :aria-label="theme === 'light' ? '切换到深色模式' : '切换到浅色模式'" :title="theme === 'light' ? '切换到深色模式' : '切换到浅色模式'" @click="toggle">
          <svg class="navbar__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
            <path v-if="theme === 'light'" d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z" />
            <g v-else>
              <circle cx="12" cy="12" r="4" />
              <path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42" />
            </g>
          </svg>
        </button>
      </div>
    </div>
  </header>
  <SearchDialog v-if="searchOpen" @close="closeSearch" />
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { createNavEntries, NAV_RIGHT_ITEMS, NAV_LOGO } from '@/config/nav';
import { useContent } from '@/composables/useContent';
import { useTheme } from '@/composables/useTheme';
import SearchDialog from './SearchDialog.vue';

const { theme, toggle } = useTheme();
const { manifest } = useContent();
const navEntries = computed(() => createNavEntries(manifest.value.tree));
const mobileOpen = ref(false);
const mobileNavToggle = ref<HTMLButtonElement | null>(null);
const route = useRoute();
const active = ref<string | null>(null);
const searchOpen = ref(false);
const searchToggle = ref<HTMLButtonElement | null>(null);
watch(() => route.fullPath, () => { mobileOpen.value = false; active.value = null; searchOpen.value = false; });
let timer: number | null = null;

function openSearch() {
  mobileOpen.value = false;
  active.value = null;
  searchOpen.value = true;
}
async function closeSearch() {
  searchOpen.value = false;
  await nextTick();
  searchToggle.value?.focus();
}

function inSection(rootPath: string) {
  return route.path === rootPath || route.path.startsWith(`${rootPath}/`);
}
function closeMobileMenu() {
  if (!mobileOpen.value) return;
  mobileNavToggle.value?.focus();
  mobileOpen.value = false;
}

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
  top: 0; left: 0; right: 0;
  height: var(--ifm-navbar-height);
  background: var(--site-background);
  border-bottom: 1px solid var(--site-border);
  z-index: 1000;
}
.navbar__inner {
  max-width: 1320px;
  margin: 0 auto;
  height: 100%;
  padding: 0 24px;
  display: flex;
  align-items: center;
  gap: 24px;
}

/* Brand / Logo */
.navbar__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: inherit;
}
.navbar__logo {
  width: 28px;
  height: 28px;
  border-radius: 6px;
}
.navbar__title {
  font-size: 1rem;
  font-weight: 750;
  letter-spacing: 0.02em;
  color: var(--site-text);
}

/* Nav items */
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
  border-radius: 7px;
  transition: color 180ms, background 180ms;
  cursor: pointer;
  background: transparent;
  text-decoration: none;
}
.navbar__link:hover {
  color: var(--ifm-color-primary);
  background: var(--site-accent-soft);
}
.navbar__home.router-link-exact-active { color: var(--ifm-color-primary); background: var(--site-accent-soft); }
.navbar__link--active { color: var(--ifm-color-primary); background: var(--site-accent-soft); }
.navbar__icon-button { width: 44px; height: 44px; padding: 0; justify-content: center; flex-shrink: 0; }
.navbar__icon { display: block; width: 22px; height: 22px; }

.caret {
  display: inline-block;
  width: 0; height: 0;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-top: 5px solid currentColor;
  opacity: 0.6;
  margin-left: 2px;
}

/* Dropdown */
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
  font-size: 0.82rem;
  font-weight: 500;
  line-height: 1.35;
  text-decoration: none;
}
.dropdown__link:hover,
.dropdown__link.router-link-active {
  background: var(--site-accent-soft);
  color: var(--ifm-color-primary-dark);
  font-weight: 600;
}

.mobile-nav-toggle { display: none; }
.search-toggle { min-height: 44px; }

@media (max-width: 996px) {
  .navbar__items--left { display: none; }
  .navbar__items--left .navbar__link { min-height: 44px; }
  .navbar__inner { gap: 12px; padding: 0 12px; }
  .navbar__items--right { margin-left: auto; gap: 4px; }
  .navbar__items--right > a { display: none; }
  .mobile-nav-toggle { display: inline-flex; align-items: center; min-height: 44px; }
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
    box-shadow: 0 16px 28px var(--site-shadow);
  }
  .dropdown__menu { position: static; box-shadow: none; margin: 0 8px 8px; }
  .dropdown__link { display: flex; align-items: center; min-height: 44px; }
}
</style>
