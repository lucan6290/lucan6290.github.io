<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  NModal,
  NForm,
  NFormItem,
  NSelect,
  NInput,
  NInputNumber,
  NDatePicker,
  NButton,
  NSpace,
  NTag,
  useMessage,
  type SelectOption
} from 'naive-ui'
import { getAPI } from '@/api'
import type { PostDetail } from '@/types/api'
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

const typeOptions: SelectOption[] = [
  { label: 'Docs 知识库', value: 'docs' },
  { label: 'Blog 博客', value: 'blog' }
]

const articleType = ref<'docs' | 'blog'>('docs')
const title = ref('')
const slug = ref('')
const description = ref('')
const primaryCategory = ref('')
const secondaryCategory = ref('')
const sidebarPosition = ref<number | null>(null)
const authorsText = ref('lucan')
const tagValues = ref<string[]>([])
const tagOptions = ref<SelectOption[]>([])
const dateTimestamp = ref<number | null>(Date.now())
const date = ref(formatLocalDateTime(Date.now()))
const loading = ref(false)

const unsafePathCharsPattern = /[<>:"\\|?*\x00-\x1f/]/

const primaryCategoryOptions = computed<SelectOption[]>(() => {
  const options = new Map<string, SelectOption>()

  for (const category of categoriesStore.allCategories) {
    if (!category.enabled || category.type !== articleType.value) continue
    options.set(category.slug, {
      label: category.name,
      value: category.slug
    })
  }

  return [...options.values()]
})

const secondaryCategoryOptions = computed<SelectOption[]>(() => {
  if (!primaryCategory.value) return []

  const selectedPrimary = categoriesStore.allCategories.find(
    (category) =>
      category.type === articleType.value &&
      category.enabled &&
      category.slug === primaryCategory.value
  )
  const options = new Map<string, SelectOption>()

  for (const sub of selectedPrimary?.subCategories || []) {
    if (!sub.enabled) continue
    options.set(sub.slug, {
      label: sub.name,
      value: sub.slug
    })
  }

  return [...options.values()]
})

const slugError = computed(() => {
  return validatePathSegment(slug.value, '请输入文件名')
})

const categoryPath = computed(() =>
  [primaryCategory.value, secondaryCategory.value]
    .map(item => item.trim())
    .filter(Boolean)
)

const categoryError = computed(() => {
  if (articleType.value !== 'docs') return ''
  if (!primaryCategory.value.trim()) return '请选择或输入一级分类'
  for (const item of categoryPath.value) {
    const error = validatePathSegment(item, '分类不能为空')
    if (error) return `分类名称不合法：${item}（${error}）`
  }
  return ''
})

const authors = computed(() =>
  authorsText.value.split(/[,，]/).map(item => item.trim()).filter(Boolean)
)

const tags = computed(() =>
  tagValues.value.map(item => item.trim()).filter(Boolean)
)

const blogError = computed(() => {
  if (articleType.value !== 'blog') return ''
  if (authors.value.length === 0) return 'blog 文章必须填写作者'
  if (tags.value.length === 0) return 'blog 文章必须填写标签'
  if (!date.value || !/^\d{4}-\d{2}-\d{2}/.test(date.value)) return '请选择发布时间'
  return ''
})

const formValid = computed(() =>
  Boolean(title.value.trim() && !slugError.value && !categoryError.value && !blogError.value)
)

const targetPath = computed(() => {
  if (!slug.value.trim()) return ''
  if (articleType.value === 'docs') {
    return [...categoryPath.value, `${slug.value.trim()}.md`].join('/')
  }
  return `${date.value || 'YYYY-MM-DD'}-${slug.value.trim()}.md`
})

watch(
  () => props.show,
  (visible) => {
    if (!visible) resetForm()
  }
)

watch(articleType, () => {
  primaryCategory.value = ''
  secondaryCategory.value = ''
})

watch(primaryCategory, () => {
  secondaryCategory.value = ''
})

watch(title, (value) => {
  if (slug.value.trim()) return
  slug.value = normalizePathSegment(value)
})

onMounted(() => {
  categoriesStore.fetchRegistry().catch(() => {
    message.warning('分类注册表加载失败，可手动输入分类路径')
  })
  loadTags()
})

function resetForm() {
  articleType.value = 'docs'
  title.value = ''
  slug.value = ''
  description.value = ''
  primaryCategory.value = ''
  secondaryCategory.value = ''
  sidebarPosition.value = null
  authorsText.value = 'lucan'
  tagValues.value = []
  dateTimestamp.value = Date.now()
  date.value = formatLocalDateTime(dateTimestamp.value)
  loading.value = false
}

function normalizePathSegment(value: string): string {
  return value
    .trim()
    .replace(/\.[^.]+$/, '')
    .replace(/[<>:"\\|?*\x00-\x1f/]+/g, '-')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^[.\s-]+|[.\s-]+$/g, '')
}

function validatePathSegment(value: string, emptyMessage: string): string {
  const normalized = value.trim()
  if (!normalized) return emptyMessage
  if (normalized === '.' || normalized === '..') return '不能使用 . 或 ..'
  if (unsafePathCharsPattern.test(normalized)) return '不能包含 / \\ : * ? " < > | 等路径字符'
  if (/[.\s]$/.test(normalized)) return '不能以空格或点号结尾'
  if (normalized.length > 120) return '不能超过 120 个字符'
  return ''
}

function formatLocalDateTime(timestamp: number): string {
  const dateValue = new Date(timestamp)
  const pad = (value: number) => String(value).padStart(2, '0')
  const offsetMinutes = -dateValue.getTimezoneOffset()
  const sign = offsetMinutes >= 0 ? '+' : '-'
  const offsetHours = Math.floor(Math.abs(offsetMinutes) / 60)
  const offsetRemainMinutes = Math.abs(offsetMinutes) % 60
  return [
    `${dateValue.getFullYear()}-${pad(dateValue.getMonth() + 1)}-${pad(dateValue.getDate())}`,
    `T${pad(dateValue.getHours())}:${pad(dateValue.getMinutes())}:${pad(dateValue.getSeconds())}`,
    `${sign}${pad(offsetHours)}:${pad(offsetRemainMinutes)}`
  ].join('')
}

function handleDateChange(value: number | null) {
  dateTimestamp.value = value
  date.value = value ? formatLocalDateTime(value) : ''
}

async function loadTags() {
  try {
    const api = getAPI()
    const tags = api.getTags ? await api.getTags({ pageSize: 200, sort: 'label' }) : []
    tagOptions.value = tags.map((tag) => ({
      label: tag.label,
      value: tag.label
    }))
  } catch {
    tagOptions.value = []
  }
}

function handleClose() {
  emit('update:show', false)
  resetForm()
}

async function handleCreate() {
  if (!formValid.value) {
    message.warning(slugError.value || categoryError.value || blogError.value || '请填写完整信息')
    return
  }

  loading.value = true
  try {
    const api = getAPI()
    const detail = await api.createPost('', '', {
      type: articleType.value,
      title: title.value.trim(),
      slug: slug.value.trim(),
      description: description.value.trim() || null,
      categoryPath: articleType.value === 'docs' ? categoryPath.value : [],
      sidebarPosition: articleType.value === 'docs' ? sidebarPosition.value : null,
      authors: articleType.value === 'blog' ? authors.value : [],
      tags: articleType.value === 'blog' ? tags.value : [],
      date: articleType.value === 'blog' ? date.value || null : null
    }) as PostDetail

    message.success('文章创建成功')
    if (articleType.value === 'docs') {
      categoriesStore.fetchRegistry(true).catch(() => undefined)
    }
    handleClose()
    router.push({
      path: '/editor',
      query: { file: detail.path }
    })
  } catch (error: any) {
    console.error('创建文章失败:', error)
    const errorMessage = error.message || '创建文章失败'
    message.error(errorMessage.includes('已存在') ? '文件名已存在，请更改名称后重试' : errorMessage)
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
    class="new-post-modal"
    style="width: min(600px, calc(100vw - 32px))"
    :mask-closable="false"
  >
    <NForm class="new-post-form" label-placement="left" label-width="92px" size="medium" :show-require-mark="false">
      <div class="field-grid">
        <NFormItem label="文章类型" required>
          <NSelect v-model:value="articleType" :options="typeOptions" />
        </NFormItem>

        <NFormItem v-if="articleType === 'docs'" label="排序">
          <NInputNumber v-model:value="sidebarPosition" :min="1" clearable placeholder="可选" />
        </NFormItem>

        <NFormItem v-if="articleType === 'blog'" label="发布时间">
          <NDatePicker
            :value="dateTimestamp"
            type="datetime"
            clearable
            format="yyyy-MM-dd HH:mm"
            placeholder="选择发布时间"
            @update:value="handleDateChange"
          />
        </NFormItem>
      </div>

      <NFormItem label="标题" required>
        <NInput v-model:value="title" placeholder="请输入文章标题" clearable />
      </NFormItem>

      <NFormItem label="文件名" required :validation-status="slugError ? 'error' : undefined" :feedback="slugError || '支持中文文件名；会生成 .md 文件'">
        <NInput v-model:value="slug" placeholder="例如 测试 或 fastapi-api-design" clearable />
      </NFormItem>

      <NFormItem label="描述">
        <NInput v-model:value="description" type="textarea" :rows="1" placeholder="可选，最多 300 字" />
      </NFormItem>

      <NFormItem
        v-if="articleType === 'docs'"
        label="一级分类"
        :validation-status="categoryError ? 'error' : undefined"
        :feedback="categoryError || '可选择现有分类，也可直接输入新分类'"
      >
        <NSelect
          v-model:value="primaryCategory"
          :options="primaryCategoryOptions"
          placeholder="选择或输入一级分类"
          filterable
          tag
          clearable
        />
      </NFormItem>

      <NFormItem
        v-if="articleType === 'docs'"
        label="二级分类"
        :validation-status="categoryError ? 'error' : undefined"
        :feedback="categoryError || '可选；可选择现有二级分类，也可输入中文新分类'"
      >
        <NSelect
          v-model:value="secondaryCategory"
          :options="secondaryCategoryOptions"
          placeholder="选择或输入二级分类"
          filterable
          tag
          clearable
          :disabled="!primaryCategory"
        />
      </NFormItem>

      <NFormItem v-if="articleType === 'blog'" label="作者" required>
        <NInput v-model:value="authorsText" placeholder="多个作者用逗号分隔" clearable />
      </NFormItem>

      <NFormItem
        v-if="articleType === 'blog'"
        label="标签"
        required
        :validation-status="blogError ? 'error' : undefined"
        :feedback="blogError || undefined"
      >
        <NSelect
          v-model:value="tagValues"
          :options="tagOptions"
          placeholder="选择或输入标签"
          multiple
          filterable
          tag
          clearable
        />
      </NFormItem>

      <NFormItem label="预览">
        <div class="preview-panel">
          <div class="preview-line">
            <span class="preview-label">接口</span>
            <NTag size="small" type="info">POST /api/v1/articles</NTag>
          </div>
          <div class="preview-line">
            <span class="preview-label">目标文件</span>
            <NTag v-if="targetPath" size="small" type="success">{{ targetPath }}</NTag>
            <span v-else class="preview-empty">等待输入...</span>
          </div>
        </div>
      </NFormItem>
    </NForm>

    <template #footer>
      <NSpace justify="end">
        <NButton @click="handleClose">取消</NButton>
        <NButton type="primary" :loading="loading" :disabled="!formValid" @click="handleCreate">
          创建
        </NButton>
      </NSpace>
    </template>
  </NModal>
</template>

<style scoped>
.new-post-modal :deep(.n-card-header) {
  padding: 16px 18px 8px;
}

.new-post-modal :deep(.n-card-header__main) {
  font-size: 17px;
  font-weight: 700;
}

.new-post-modal :deep(.n-card__content) {
  max-height: min(70vh, 620px);
  padding: 8px 18px 2px;
  overflow-y: auto;
}

.new-post-modal :deep(.n-card__footer) {
  padding: 10px 18px 16px;
}

.new-post-form {
  padding-top: 0;
}

.new-post-form :deep(.n-form-item) {
  --n-feedback-height: 18px;
  margin-bottom: 2px;
}

.new-post-form :deep(.n-form-item-label) {
  font-weight: 600;
}

.field-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(150px, 0.75fr);
  column-gap: 12px;
}

.preview-panel {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid rgba(74, 98, 86, 0.14);
  border-radius: 8px;
  background: rgba(248, 250, 246, 0.9);
}

.preview-line {
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr);
  align-items: center;
  min-height: 26px;
  gap: 8px;
}

.preview-label {
  color: #66746c;
  font-size: 12px;
  font-weight: 700;
}

.preview-empty {
  color: #9aa59f;
  font-size: 13px;
}

.new-post-form :deep(.n-input-number) {
  width: 100%;
}

.new-post-form :deep(.n-date-picker) {
  width: 100%;
}

.new-post-form :deep(.n-tag) {
  max-width: 100%;
  white-space: normal;
  word-break: break-all;
}

@media (max-width: 640px) {
  .new-post-modal :deep(.n-card__content) {
    max-height: 76vh;
    padding-inline: 14px;
  }

  .new-post-modal :deep(.n-card-header),
  .new-post-modal :deep(.n-card__footer) {
    padding-inline: 14px;
  }

  .new-post-form {
    --n-label-width: 78px;
  }

  .field-grid {
    grid-template-columns: 1fr;
    row-gap: 0;
  }
}

</style>
