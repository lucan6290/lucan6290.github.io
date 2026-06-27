<script setup lang="ts">
import { NTag, NSpace, NText } from 'naive-ui'

defineProps<{
  flags: string[]
  emptyText?: string
}>()
</script>

<template>
  <div class="risk-flags">
    <n-space v-if="flags.length" size="small" wrap>
      <n-tag v-for="flag in flags" :key="flag" type="warning" size="small">
        {{ flag }}
      </n-tag>
    </n-space>
    <n-text v-else depth="3" class="empty-risk">
      {{ emptyText || '暂无风险提示' }}
    </n-text>
  </div>
</template>

<style scoped>
.risk-flags {
  min-height: 26px;
}

.empty-risk {
  font-size: 12px;
}
</style>

