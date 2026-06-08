<script setup lang="ts">
import { ref } from 'vue'
import { NH1, NP, NButton, NSpace } from 'naive-ui'
import NewPostModal from '@/components/NewPostModal.vue'

const showNewPostModal = ref(false)
</script>

<template>
  <div class="home">
    <n-h1>博客管理后台</n-h1>
    <n-p>欢迎使用博客管理后台系统</n-p>
    
    <n-space style="margin-top: 20px">
      <n-button type="primary" @click="showNewPostModal = true">
        新建文章
      </n-button>
    </n-space>

    <NewPostModal v-model:show="showNewPostModal" />
  </div>
</template>

<style scoped>
.home {
  padding: 20px;
}
</style>