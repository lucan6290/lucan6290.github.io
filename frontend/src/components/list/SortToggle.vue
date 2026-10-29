<template>
  <button class="sort-toggle" type="button" @click="$emit('toggle')">
    排序：{{ mode === 'prefix' ? '目录顺序' : '创建时间' }}
  </button>
</template>

<script setup lang="ts">
defineProps<{ mode: 'prefix' | 'date' }>();
defineEmits<{ toggle: [] }>();
</script>

<style scoped>
.sort-toggle {
  padding: 6px 14px;
  border-radius: 999px;
  background: var(--site-accent-soft);
  color: var(--ifm-color-primary);
  font-size: 0.82rem;
  font-weight: 600;
  transition: background 180ms;
}
.sort-toggle:hover { background: var(--site-border); }
</style>
