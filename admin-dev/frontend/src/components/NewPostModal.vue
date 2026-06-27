<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  NModal,
  NForm,
  NFormItem,
  NSelect,
  NInput,
  NButton,
  NSpace,
  NDescriptions,
  NDescriptionsItem,
  NTag,
  useMessage,
  type SelectOption
} from 'naive-ui'
import { getAPI } from '@/api'
import { useCategoriesStore } from '@/stores/categories'

interface Props {
  show: boolean
}

const emit = defineEmits<{
  'update:show': [value: boolean]
}>()

const props = defineProps<Props>()
const router = useRouter()
const message = useMessage()
const categoriesStore = useCategoriesStore()

const selectedPrimaryPrefix = ref<string | null>(null)
const selectedSecondaryPrefix = ref<string | null>(null)
const newSecondaryName = ref('')
const title = ref('')
const loading = ref(false)

const selectedPrimaryCategory = computed(() =>
  categoriesStore.getPrimaryByPrefix(selectedPrimaryPrefix.value)
)

const selectedSecondaryCategory = computed(() =>
  categoriesStore.getSecondaryByPrefix(selectedPrimaryPrefix.value, selectedSecondaryPrefix.value)
)

const isNewSecondaryPrefix = computed(() =>
  Boolean(selectedPrimaryPrefix.value && selectedSecondaryPrefix.value && !selectedSecondaryCategory.value)
)

const primaryCategoryOptions = computed<SelectOption[]>(() => categoriesStore.enabledPrimaryCategories)

const secondaryCategoryOptions = computed<SelectOption[]>(() => {
  const primary = selectedPrimaryCategory.value
  if (!primary) return []

  return primary.children
    .filter((child) => child.enabled)
    .map((child) => ({
      label: `${child.frontend_name2} (${child.note_prefix2})`,
      value: child.note_prefix2
    }))
})

const primaryPrefix = computed(() => selectedPrimaryCategory.value?.note_prefix1 || '')
const secondaryPrefix = computed(() => selectedSecondaryPrefix.value || '')
const secondaryFrontendName = computed(() =>
  selectedSecondaryCategory.value?.frontend_name2 || newSecondaryName.value.trim()
)

const fileName = computed(() => {
  if (!primaryPrefix.value || !secondaryPrefix.value || !title.value.trim()) return ''
  return `${primaryPrefix.value}-${secondaryPrefix.value}-${title.value.trim()}.md`
})

const filePath = computed(() => {
  if (!selectedPrimaryCategory.value || !fileName.value) return ''
  return `blog-content/source/_posts/${selectedPrimaryCategory.value.category_slug}/${fileName.value}`
})

const categoriesDisplay = computed(() => {
  if (!selectedPrimaryCategory.value || !secondaryFrontendName.value) return ''
  return `[${selectedPrimaryCategory.value.frontend_name1}, ${secondaryFrontendName.value}]`
})

const coverDisplay = computed(() => selectedPrimaryCategory.value?.cover || '')

const prefix2Error = computed(() => {
  if (!selectedSecondaryPrefix.value) return ''
  if (selectedSecondaryPrefix.value.includes('-')) return '二级分类文件名前缀不能包含连字符(-)'
  if (!/^[A-Za-z0-9_]+$/.test(selectedSecondaryPrefix.value)) {
    return '二级分类文件名前缀只能使用英文、数字或下划线'
  }
  return ''
})

const formValid = computed(() =>
  Boolean(
    selectedPrimaryCategory.value &&
      selectedSecondaryPrefix.value &&
      !prefix2Error.value &&
      title.value.trim() &&
      (!isNewSecondaryPrefix.value || newSecondaryName.value.trim())
  )
)

watch(selectedPrimaryPrefix, () => {
  selectedSecondaryPrefix.value = null
  newSecondaryName.value = ''
})

watch(selectedSecondaryPrefix, () => {
  newSecondaryName.value = ''
})

watch(
  () => props.show,
  async (visible) => {
    if (visible) {
      await categoriesStore.fetchRegistry(true)
    }
  }
)

const handleClose = () => {
  emit('update:show', false)
  resetForm()
}

const resetForm = () => {
  selectedPrimaryPrefix.value = null
  selectedSecondaryPrefix.value = null
  newSecondaryName.value = ''
  title.value = ''
}

const handleCreate = async () => {
  if (!formValid.value) {
    message.warning(prefix2Error.value || '请填写完整信息')
    return
  }

  loading.value = true

  try {
    if (isNewSecondaryPrefix.value) {
      const added = await categoriesStore.addSecondaryCategory(primaryPrefix.value, {
        frontend_name2: newSecondaryName.value.trim(),
        note_prefix2: secondaryPrefix.value
      })

      if (!added) {
        message.error('新增二级分类失败，请检查文件名前缀是否重复')
        return
      }
    }

    const path = `${selectedPrimaryCategory.value!.category_slug}/${fileName.value}`
    const api = getAPI()
    await api.createPost(path, '', {
      title: title.value.trim(),
      prefix1: primaryPrefix.value,
      prefix2: secondaryPrefix.value
    })

    message.success('文章创建成功')
    handleClose()
    router.push({
      path: '/editor',
      query: { file: path }
    })
  } catch (error: any) {
    console.error('创建文章失败:', error)
    message.error(error.message || '创建文章失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <NModal
    :show="show"
    @update:show="emit('update:show', $event)"
    preset="card"
    title="新建文章"
    style="width: 800px; max-width: 90vw"
    :mask-closable="false"
  >
    <NForm class="new-post-form" label-placement="left" label-width="120px">
      <NFormItem label="一级分类" required>
        <NSelect
          v-model:value="selectedPrimaryPrefix"
          :options="primaryCategoryOptions"
          placeholder="请选择一级分类"
          :loading="categoriesStore.isLoading"
          style="width: 100%"
        />
      </NFormItem>

      <NFormItem
        label="二级文件前缀"
        required
        :validation-status="prefix2Error ? 'error' : undefined"
        :feedback="prefix2Error"
      >
        <NSelect
          v-model:value="selectedSecondaryPrefix"
          :options="secondaryCategoryOptions"
          placeholder="选择已有二级分类，或输入新的 note_prefix2"
          :disabled="!selectedPrimaryPrefix"
          filterable
          tag
          style="width: 100%"
        />
      </NFormItem>

      <NFormItem v-if="isNewSecondaryPrefix" label="二级显示名" required>
        <NInput
          v-model:value="newSecondaryName"
          placeholder="例如：AI 探索。将同步写入分类管理"
          clearable
        />
      </NFormItem>

      <NFormItem label="文章标题" required>
        <NInput
          v-model:value="title"
          placeholder="请输入文章标题"
          clearable
          @keydown.enter.prevent
        />
      </NFormItem>

      <NFormItem label="预览">
        <NDescriptions label-placement="left" bordered :column="1">
          <NDescriptionsItem label="文件名">
            <NTag v-if="fileName" type="info">{{ fileName }}</NTag>
            <span v-else style="color: #999">等待输入...</span>
          </NDescriptionsItem>
          <NDescriptionsItem label="文件路径">
            <NTag v-if="filePath" type="success">{{ filePath }}</NTag>
            <span v-else style="color: #999">等待输入...</span>
          </NDescriptionsItem>
          <NDescriptionsItem label="分类">
            <NTag v-if="categoriesDisplay" type="warning">{{ categoriesDisplay }}</NTag>
            <span v-else style="color: #999">等待选择...</span>
          </NDescriptionsItem>
          <NDescriptionsItem label="封面">
            <NTag v-if="coverDisplay" type="default">{{ coverDisplay }}</NTag>
            <span v-else style="color: #999">等待选择...</span>
          </NDescriptionsItem>
          <NDescriptionsItem label="状态">
            <NTag type="default">draft</NTag>
          </NDescriptionsItem>
        </NDescriptions>
      </NFormItem>
    </NForm>

    <template #footer>
      <NSpace justify="end">
        <NButton @click="handleClose">取消</NButton>
        <NButton
          type="primary"
          @click="handleCreate"
          :loading="loading"
          :disabled="!formValid"
        >
          创建
        </NButton>
      </NSpace>
    </template>
  </NModal>
</template>

<style scoped>
.new-post-form {
  padding-top: 4px;
}

.new-post-form :deep(.n-descriptions) {
  overflow: hidden;
  border-radius: 12px;
  box-shadow: var(--admin-shadow-sm);
}

.new-post-form :deep(.n-descriptions-table-content) {
  background: rgba(251, 252, 248, 0.94);
  font-weight: 500;
}

.new-post-form :deep(.n-descriptions-table-header) {
  color: #40534a;
  background: #f2f6ef;
  font-weight: 600;
}

.new-post-form :deep(.n-tag) {
  max-width: 100%;
  white-space: normal;
  word-break: break-all;
}
</style>
