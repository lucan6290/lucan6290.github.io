<script setup lang="ts">
import { computed } from 'vue'
import { NAlert, NRadioButton, NRadioGroup, NSpace, NText } from 'naive-ui'
import type { AIApprovalMode } from '@/types/ai-writing'

const props = withDefaults(defineProps<{
  value: AIApprovalMode
  effectiveValue?: AIApprovalMode
  downgraded?: boolean
  reasons?: string[]
  disabled?: boolean
}>(), {
  effectiveValue: undefined,
  downgraded: false,
  reasons: () => [],
  disabled: false
})

const emit = defineEmits<{
  (event: 'update:value', value: AIApprovalMode): void
}>()

const currentValue = computed({
  get: () => props.value,
  set: (value: AIApprovalMode) => emit('update:value', value)
})

const hint = computed(() => {
  if (props.value === 'request-approval') return 'AI 只生成方案或建议，写入前需要你确认。'
  if (props.value === 'delegate-approval') return '低风险且校验通过时可自动采纳。'
  return '仅在当前 AI 写作任务内自动执行，不包含发布、Git、删除等系统操作。'
})
</script>

<template>
  <div class="approval-mode-select">
    <n-radio-group v-model:value="currentValue" :disabled="disabled" size="small">
      <n-space size="small">
        <n-radio-button value="request-approval">请求批准</n-radio-button>
        <n-radio-button value="delegate-approval">替我审批</n-radio-button>
        <n-radio-button value="full-access">完全访问权限</n-radio-button>
      </n-space>
    </n-radio-group>

    <n-text depth="3" class="approval-hint">{{ hint }}</n-text>

    <n-alert
      v-if="downgraded || effectiveValue === 'request-approval' && value !== 'request-approval'"
      type="warning"
      size="small"
      :show-icon="false"
      class="approval-alert"
    >
      已降级为请求批准{{ reasons.length ? `：${reasons.join('；')}` : '' }}
    </n-alert>
  </div>
</template>

<style scoped>
.approval-mode-select {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.approval-hint {
  font-size: 12px;
  line-height: 1.5;
}

.approval-alert {
  border-radius: 8px;
}
</style>

