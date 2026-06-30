<script setup lang="ts">
import { NAlert } from 'naive-ui'
import type { AIWritingError } from '@/types/ai-writing'

withDefaults(defineProps<{
  error: AIWritingError | null
  compact?: boolean
}>(), {
  compact: false
})
</script>

<template>
  <n-alert
    v-if="error"
    type="error"
    :title="error.title"
    :show-icon="!compact"
    class="error-state"
  >
    <div>{{ error.message }}</div>
    <div v-if="error.details" class="error-details">{{ error.details }}</div>
  </n-alert>
</template>

<style scoped>
.error-state {
  border-radius: 8px;
}

.error-details {
  margin-top: 6px;
  font-size: 12px;
  opacity: 0.78;
}
</style>

