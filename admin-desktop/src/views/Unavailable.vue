<script setup lang="ts">
import { useRoute } from 'vue-router'
const route = useRoute()
</script>
<template>
  <div>
    <div class="main-header"><div class="main-header-title">{{ route.meta.title }}</div></div>
    <div class="main-content"><div class="card"><h3>尚未适配新内容库</h3><p>此功能将在后续阶段接入。当前可在文档管理中创建和编辑 Markdown，也可以通过外部编辑器或 AI 修改文件。</p><router-link class="btn btn-primary" to="/posts">打开文档管理</router-link></div></div>
  </div>
</template>
