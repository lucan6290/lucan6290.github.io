<template>
  <nav class="tree-sidebar" aria-label="目录导航">
    <ul class="menu">
      <SidebarNode
        v-for="node in nodes"
        :key="node.path"
        :node="node"
        :active-path="activePath"
        :depth="0"
      />
    </ul>
  </nav>
</template>

<script setup lang="ts">
import SidebarNode from './SidebarNode.vue';
import type { TreeNode } from '@/types/content';

defineProps<{ nodes: TreeNode[]; activePath: string; root: string }>();
</script>

<style scoped>
.tree-sidebar { font-size: 14px; }
.menu { list-style: none; padding: 0; margin: 0; }
</style>
