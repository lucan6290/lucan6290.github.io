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
        <button ref="mobileNavToggle" class="navbar__link mobile-nav-toggle" type="button" aria-controls="section-navigation" :aria-expanded="mobileOpen" @click="mobileOpen = !mobileOpen" @keydown.esc="closeMobileMenu">栏目</button>
        <a
          v-for="item in NAV_RIGHT_ITEMS"
          :key="item.href"
          class="navbar__link"
          :href="item.href"
          target="_blank"
          rel="noopener"
        >{{ item.label }}</a>
        <button class="theme-toggle" type="button" :aria-label="theme === 'light' ? '切换到深色模式' : '切换到浅色模式'" @click="toggle">
          <span v-if="theme === 'light'" aria-hidden="true">🌙</span>
          <span v-else aria-hidden="true">☀️</span>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { createNavEntries, NAV_RIGHT_ITEMS, NAV_LOGO } from '@/config/nav';
import { useContent } from '@/composables/useContent';
import { useTheme } from '@/composables/useTheme';

const { theme, toggle } = useTheme();
const { manifest } = useContent();
const navEntries = computed(() => createNavEntries(manifest.value.tree));
const mobileOpen = ref(false);
const mobileNavToggle = ref<HTMLButtonElement | null>(null);
const route = useRoute();
const active = ref<string | null>(null);
watch(() => route.fullPath, () => { mobileOpen.value = false; active.value = null; });
let timer: number | null = null;

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

/* Theme toggle */
.theme-toggle {
  width: 44px; height: 44px;
  border-radius: 9px;
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
