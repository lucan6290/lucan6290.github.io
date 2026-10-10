<template>
  <div class="app-shell">
    <Navbar />
    <main class="app-main">
      <slot />
    </main>
    <Footer v-if="showFooter" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import Navbar from './Navbar.vue';
import Footer from './Footer.vue';

const route = useRoute();
const showFooter = computed(() => route.path === '/');
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.app-main {
  flex: 1;
  margin-top: var(--ifm-navbar-height);
}
</style>
