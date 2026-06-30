<script setup lang="ts">
import { computed } from 'vue'
import { NButton, NSpace } from 'naive-ui'
import type { AIWritingMode } from '@/types/ai-writing'

const props = withDefaults(defineProps<{
  value: AIWritingMode
  disabled?: boolean
}>(), {
  disabled: false
})

const emit = defineEmits<{
  (event: 'update:value', value: AIWritingMode): void
}>()

const currentValue = computed({
  get: () => props.value,
  set: (value: AIWritingMode) => emit('update:value', value)
})

const modes: Array<{ label: string; value: AIWritingMode; caption: string }> = [
  { label: 'Agent 模式', value: 'agent', caption: '从想法到草稿' },
  { label: '知识库稳定模式', value: 'knowledge', caption: '只读问答与引用' }
]
</script>

<template>
  <n-space class="mode-switch" :size="10">
    <n-button
      v-for="mode in modes"
      :key="mode.value"
      :type="currentValue === mode.value ? 'primary' : 'default'"
      :secondary="currentValue !== mode.value"
      :disabled="disabled"
      class="mode-button"
      @click="currentValue = mode.value"
    >
      <span class="mode-label">{{ mode.label }}</span>
      <span class="mode-caption">{{ mode.caption }}</span>
    </n-button>
  </n-space>
</template>

<style scoped>
.mode-switch {
  flex-wrap: wrap;
}

.mode-button {
  min-width: 174px;
  height: 58px;
  justify-content: flex-start;
}

.mode-label,
.mode-caption {
  display: block;
  text-align: left;
}

.mode-label {
  font-weight: 800;
}

.mode-caption {
  margin-top: 2px;
  font-size: 12px;
  opacity: 0.72;
}
</style>
