<script setup lang="ts">
import { NEmpty, NTimeline, NTimelineItem } from 'naive-ui'
import type { AIOperationLogItem } from '@/types/ai-writing'

defineProps<{
  items: AIOperationLogItem[]
}>()

function timelineType(level: AIOperationLogItem['level']): 'default' | 'success' | 'warning' | 'error' | 'info' {
  if (level === 'success') return 'success'
  if (level === 'warning') return 'warning'
  if (level === 'error') return 'error'
  return 'info'
}
</script>

<template>
  <div class="operation-log">
    <n-empty v-if="items.length === 0" description="暂无操作记录" size="small" />
    <n-timeline v-else>
      <n-timeline-item
        v-for="item in items"
        :key="item.id"
        :type="timelineType(item.level)"
        :title="item.title"
        :content="item.detail"
        :time="item.time"
      />
    </n-timeline>
  </div>
</template>

<style scoped>
.operation-log {
  max-height: 320px;
  overflow: auto;
  padding-right: 4px;
}
</style>

