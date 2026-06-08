<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
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

// Props
interface Props {
  show: boolean
}

// Emits
const emit = defineEmits<{
  'update:show': [value: boolean]
}>()

const props = defineProps<Props>()
const router = useRouter()
const message = useMessage()
const categoriesStore = useCategoriesStore()
const api = getAPI()

// ============================================================
// 常量映射
// ============================================================

// 一级分类 slug → 前缀
const PREFIX_MAP: Record<string, string> = {
  'tech-study': 'ts',
  'pitfall-review': 'pr',
  'project-practice': 'pp',
  'growth-essay': 'ge',
  'resource-sharing': 'rs'
}

// 一级分类名 → slug
const CATEGORY_NAME_TO_SLUG: Record<string, string> = {
  '技术研习': 'tech-study', '踩坑复盘': 'pitfall-review',
  '项目实战': 'project-practice', '成长随笔': 'growth-essay',
  '资源分享': 'resource-sharing',
}

// 封面图配置
const coverMap: Record<string, string> = {
  'tech-study': '/img/covers/tech-study.svg',
  'pitfall-review': '/img/covers/pitfall-review.svg',
  'project-practice': '/img/covers/project-practice.svg',
  'growth-essay': '/img/covers/growth-essay.svg',
  'resource-sharing': '/img/covers/resource-sharing.svg'
}

// ============================================================
// 从已有文章文件名中提取的 prefix2 列表
// key: 一级分类 slug (如 tech-study), value: string[] (如 ['ai', 'jetson', 'git'])
// ============================================================
const discoveredPrefixes: Record<string, string[]> = reactive({})

// ============================================================
// 表单数据
// ============================================================

const selectedPrimarySlug = ref<string | null>(null)
const selectedPrefix2 = ref<string | null>(null)  // 英文简写，直接传给 hexo np
const title = ref('')
const loading = ref(false)

// ============================================================
// 计算属性
// ============================================================

// 一级分类选项（从 store 获取）
const primaryCategoryOptions = computed<SelectOption[]>(() => {
  return categoriesStore.primaryCategories
})

// 一级分类前缀
const primaryPrefix = computed(() => {
  return PREFIX_MAP[selectedPrimarySlug.value!] || ''
})

// 二级分类选项：从已有文章文件名中提取的 prefix2（过滤含 - 的值）
const secondaryCategoryOptions = computed<SelectOption[]>(() => {
  if (!selectedPrimarySlug.value) return []

  const prefixes = discoveredPrefixes[selectedPrimarySlug.value] || []
  return [...new Set(prefixes)]
    .filter(p => !p.includes('-'))   // 只保留不含 - 的 prefix2，确保文件名只有两个分隔符
    .sort()
    .map(p => ({ label: p, value: p }))
})

// 获取一级分类信息
const selectedPrimaryCategory = computed(() => {
  if (!selectedPrimarySlug.value) return null
  return categoriesStore.allCategories.find(c => c.slug === selectedPrimarySlug.value)
})

// 生成的文件名
const fileName = computed(() => {
  if (!primaryPrefix.value || !selectedPrefix2.value || !title.value.trim()) return ''
  return `${primaryPrefix.value}-${selectedPrefix2.value}-${title.value.trim()}.md`
})

// 文件路径
const filePath = computed(() => {
  if (!selectedPrimarySlug.value || !fileName.value) return ''
  return `source/_posts/${selectedPrimarySlug.value}/${fileName.value}`
})

// 分类显示（预览用，一级中文 + 二级简写）
const categoriesDisplay = computed(() => {
  if (!selectedPrimarySlug.value || !selectedPrefix2.value) return ''
  const primary = selectedPrimaryCategory.value
  return `[${primary?.name || ''}, ${selectedPrefix2.value}]`
})

// 封面显示
const coverDisplay = computed(() => {
  if (!selectedPrimarySlug.value) return ''
  return coverMap[selectedPrimarySlug.value] || ''
})

// 表单验证
const formValid = computed(() => {
  const p2 = selectedPrefix2.value
  return selectedPrimarySlug.value && p2 && !p2.includes('-') && title.value.trim()
})

// prefix2 校验提示
const prefix2Error = computed(() => {
  if (!selectedPrefix2.value) return ''
  if (selectedPrefix2.value.includes('-')) return '二级分类不能包含连字符(-)'
  return ''
})

// ============================================================
// 监听
// ============================================================

// 一级分类变化时重置二级分类
watch(selectedPrimarySlug, () => {
  selectedPrefix2.value = null
})

// 弹窗打开时拉取文章列表，从中提取 prefix2
watch(
  () => props.show,
  async (visible) => {
    if (visible) {
      try {
        const posts = await api.getPosts()
        extractPrefixesFromPosts(posts as any[])
      } catch {}
    }
  }
)

// ============================================================
// 方法
// ============================================================

/**
 * 从文章列表中提取每个一级分类下的 prefix2 值
 * 通过解析 filename（如 ts-ai-agent入门笔记 → prefix2=ai）
 */
function extractPrefixesFromPosts(posts: any[]) {
  const map: Record<string, Set<string>> = {}

  for (const post of posts) {
    const filename: string = post.filename || ''
    const category: string = post.category || ''  // 一级分类 slug，如 tech-study
    const prefix1 = PREFIX_MAP[category]
    if (!prefix1 || !filename.startsWith(prefix1 + '-')) continue

    // 去掉 prefix1- 前缀，剩下 {prefix2}-{title}
    const rest = filename.slice(prefix1.length + 1)
    // prefix2 是第一个 - 之前的部分
    const dashIdx = rest.indexOf('-')
    const prefix2 = dashIdx > 0 ? rest.slice(0, dashIdx) : rest

    if (!map[category]) map[category] = new Set()
    map[category].add(prefix2)
  }

  // 写入 reactive
  for (const slug of Object.keys(map)) {
    discoveredPrefixes[slug] = [...map[slug]]
  }
}

// 关闭弹窗
const handleClose = () => {
  emit('update:show', false)
  resetForm()
}

// 重置表单
const resetForm = () => {
  selectedPrimarySlug.value = null
  selectedPrefix2.value = null
  title.value = ''
}

// 创建文章
const handleCreate = async () => {
  if (!formValid.value) {
    if (selectedPrefix2.value?.includes('-')) {
      message.warning('二级分类不能包含连字符(-)，请使用纯英文单词')
    } else {
      message.warning('请填写完整信息')
    }
    return
  }

  loading.value = true

  try {
    // 构建文件路径（仅用于前端跳转）
    const path = `${selectedPrimarySlug.value}/${fileName.value}`

    // 调用 API 创建文章，只需 3 个参数（hexo np 自动处理模板/分类/封面）
    const api = getAPI()
    await api.createPost(path, '', {
      title: title.value.trim(),
      prefix1: primaryPrefix.value,
      prefix2: selectedPrefix2.value!,
    })

    message.success('文章创建成功')
    handleClose()

    // 跳转到编辑器
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
    <NForm label-placement="left" label-width="100px">
      <!-- 一级分类选择器 -->
      <NFormItem label="一级分类" required>
        <NSelect
          v-model:value="selectedPrimarySlug"
          :options="primaryCategoryOptions"
          placeholder="请选择一级分类"
          style="width: 100%"
        />
      </NFormItem>

      <!-- 二级分类选择器（prefix2，从已有文章文件名提取 + 可手动输入） -->
      <NFormItem label="二级分类" required :validation-status="prefix2Error ? 'error' : undefined" :feedback="prefix2Error">
        <NSelect
          v-model:value="selectedPrefix2"
          :options="secondaryCategoryOptions"
          placeholder="选择已有分类或输入新分类（不含 -）"
          :disabled="!selectedPrimarySlug"
          filterable
          tag
          style="width: 100%"
        />
      </NFormItem>

      <!-- 标题输入框 -->
      <NFormItem label="文章标题" required>
        <NInput
          v-model:value="title"
          placeholder="请输入文章标题"
          clearable
          @keydown.enter.prevent
        />
      </NFormItem>

      <!-- 实时预览 -->
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
/* 可以添加自定义样式 */
</style>