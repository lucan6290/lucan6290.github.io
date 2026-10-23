<template>
  <li class="menu__list-item" :class="{ 'is-active': isActive, 'has-children': hasChildren }">
    <div v-if="hasChildren" class="menu__list-item-collapsible" @click="toggle">
      <router-link
        class="menu__link menu__link--sublist"
        :to="contentHref(node.path)"
        @click.stop
      >{{ node.label }}</router-link>
      <button class="menu__caret" type="button" :aria-label="expanded ? '折叠' : '展开'" :aria-expanded="expanded">
        <span class="caret-icon" :class="{ collapsed: !expanded }" aria-hidden="true" />
      </button>
    </div>
    <router-link v-else class="menu__link" :to="contentHref(node.path)">{{ node.label }}</router-link>

    <ul v-if="hasChildren && expanded" class="menu__list">
      <SidebarNode
        v-for="child in node.children"
        :key="child.path"
        :node="child"
        :active-path="activePath"
        :depth="depth + 1"
      />
    </ul>
  </li>
</template>

<script setup lang="ts">
import { computed, ref, watchEffect } from 'vue';
import type { TreeNode } from '@/types/content';
import { contentHref } from '@/composables/contentPaths';

const props = defineProps<{ node: TreeNode; activePath: string; depth: number }>();

const hasChildren = computed(() => props.node.children.length > 0);
const isActive = computed(() => props.activePath === props.node.path || props.activePath.startsWith(props.node.path + '/'));
const expanded = ref(false);

// 自动展开包含当前激活路径的节点
watchEffect(() => {
  if (isActive.value) expanded.value = true;
});

function toggle() {
  expanded.value = !expanded.value;
}
</script>

<style scoped>
.menu__list-item { margin-top: 1px; }
.menu__list { list-style: none; position: relative; margin: 2px 0 0; padding-left: 16px; }
.menu__list::before {
  content: '';
  position: absolute;
  top: 4px; bottom: 4px; left: 4px;
  width: 2px; border-radius: 2px;
  background: var(--site-border);
}

.menu__link {
  display: flex;
  align-items: flex-start;
  padding: 5px 10px;
  color: var(--site-text-muted);
  font-size: 14px;
  line-height: 1.55;
  border-radius: 6px;
  word-break: break-word;
  text-decoration: none;
  transition: color 200ms, background 200ms;
}
.menu__link:hover { color: var(--ifm-color-primary); background: var(--site-accent-soft); }

.menu__link--sublist { color: var(--site-text-secondary); font-weight: 600; }

.menu__list-item.is-active > .menu__link:not(.menu__link--sublist),
.menu__list-item.is-active > .menu__list-item-collapsible > .menu__link:not(.menu__link--sublist) {
  position: relative;
  color: var(--ifm-color-primary);
  font-weight: 600;
  background: var(--site-accent-soft);
}
.menu__list-item.is-active > .menu__link:not(.menu__link--sublist)::before {
  content: '';
  position: absolute;
  top: 4px; bottom: 4px; left: -13px;
  width: 3px; border-radius: 0 3px 3px 0;
  background: var(--ifm-color-primary);
}

.menu__list-item-collapsible {
  display: flex;
  align-items: center;
  border-radius: 6px;
}
.menu__caret {
  margin-left: auto;
  width: 28px; height: 28px;
  display: grid; place-items: center;
  border-radius: 6px;
  color: var(--site-text-muted);
}
.menu__caret:hover { background: var(--site-accent-soft); }

.caret-icon {
  display: inline-block;
  width: 12px; height: 12px;
  background: currentColor;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' stroke='currentColor' stroke-linecap='round' stroke-linejoin='round' stroke-width='2.5' viewBox='0 0 24 24'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E") no-repeat center / 100% 100%;
  -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' stroke='currentColor' stroke-linecap='round' stroke-linejoin='round' stroke-width='2.5' viewBox='0 0 24 24'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E") no-repeat center / 100% 100%;
  transform: rotate(180deg);
  transition: transform 200ms;
  opacity: 0.6;
}
.caret-icon.collapsed { transform: rotate(90deg); }
</style>
