<script setup lang="ts">
import { ref } from 'vue'
import { NH1, NP, NButton, NSpace } from 'naive-ui'
import NewPostModal from '@/components/NewPostModal.vue'

const showNewPostModal = ref(false)
</script>

<template>
  <div class="home page-shell">
    <div class="home-card glass-panel">
      <p class="page-kicker">Console</p>
      <n-h1>博客管理后台</n-h1>
      <n-p>欢迎使用博客管理后台系统</n-p>
    
      <n-space style="margin-top: 20px">
        <n-button type="primary" @click="showNewPostModal = true">
          新建文章
        </n-button>
      </n-space>
    </div>

    <NewPostModal v-model:show="showNewPostModal" />
  </div>
</template>

<style scoped>
.home {
  min-height: 100%;
}

.home-card {
  padding: 28px;
}

.home h1 {
  margin: 0;
  font-weight: 850;
}
</style>
