<template>
  <div class="reading-progress" :style="{ width: `${progress}%` }" />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue';

const progress = ref(0);

function update() {
  const h = document.documentElement;
  const scrolled = h.scrollTop || document.body.scrollTop;
  const total = h.scrollHeight - h.clientHeight;
  progress.value = total > 0 ? Math.min(100, Math.max(0, (scrolled / total) * 100)) : 0;
}

onMounted(() => window.addEventListener('scroll', update, { passive: true }));
onUnmounted(() => window.removeEventListener('scroll', update));
</script>

<style scoped>
.reading-progress {
  position: fixed;
  top: var(--ifm-navbar-height);
  left: 0;
  height: 3px;
  background: var(--ifm-color-primary);
  z-index: 999;
  transition: width 80ms linear;
}
</style>
