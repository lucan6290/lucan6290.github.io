<script setup lang="ts">
import { ref, watch } from 'vue'
import { contentApi } from '@/api/content'

const props = defineProps<{ path: string; name: string }>()
const source = ref('')
const failed = ref(false)
watch(() => props.path, (path, _previous, cleanup) => {
  const controller = new AbortController()
  source.value = ''
  failed.value = false
  cleanup(() => {
    controller.abort()
    if (source.value) URL.revokeObjectURL(source.value)
  })
  void contentApi.image(path, controller.signal).then(blob => {
    if (!controller.signal.aborted) source.value = URL.createObjectURL(blob)
  }).catch(() => {
    if (!controller.signal.aborted) failed.value = true
  })
}, { immediate: true })
</script>

<template>
  <img v-if="source && !failed" :src="source" :alt="name" @error="failed = true" />
  <span v-else role="status">{{ failed ? '无法预览图片' : '正在读取图片…' }}</span>
</template>
