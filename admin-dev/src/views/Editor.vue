<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NButton,
  NText,
  NSelect,
  NInput,
  NTag,
  NCard,
  NForm,
  NFormItem,
  NDatePicker,
  NInputNumber,
  NSpace,
  NIcon,
  NModal,
  useMessage,
  useDialog,
  type SelectOption
} from 'naive-ui'
import { Editor as ByteMDEditor } from '@bytemd/vue-next'
import gfm from '@bytemd/plugin-gfm'
import highlight from '@bytemd/plugin-highlight'
import frontmatter from '@bytemd/plugin-frontmatter'
import 'bytemd/dist/index.css'
import 'highlight.js/styles/github.css'
import { getAPI } from '@/api'
import type { PostDetail, FrontMatter } from '@/types/api'
import { parseFrontMatter, buildMarkdown, validateFrontMatter } from '@/utils/frontmatter'
import AIAssistant from '@/components/AIAssistant.vue'

// 路由
const route = useRoute()
const router = useRouter()
const message = useMessage()
const dialog = useDialog()

// API
const api = getAPI()

// 文章状态
const articlePath = ref<string>('')
const articleContent = ref<string>('')
const originalContent = ref<string>('')
const frontMatter = ref<FrontMatter>({
  title: '',
  date: '',
  categories: [],
  tags: [],
  status: 'draft'
})
const bodyContent = ref<string>('')
const isLoading = ref(false)
const isSaving = ref(false)
const saveStatus = ref<'idle' | 'saving' | 'saved'>('idle')

// 日期时间戳（用于日期选择器）
const dateTimestamp = ref<number>(Date.now())

// 状态选项
const statusOptions: SelectOption[] = [
  { label: '草稿', value: 'draft' },
  { label: '进行中', value: 'wip' },
  { label: '已发布', value: 'published' }
]

// 分类选项
const categoryOptions: SelectOption[] = [
  { label: '技术研习', value: 'tech-study' },
  { label: '踩坑复盘', value: 'pitfall-review' },
  { label: '项目实战', value: 'project-practice' },
  { label: '成长随笔', value: 'growth-essay' },
  { label: '资源分享', value: 'resource-sharing' }
]

// 中文名 ↔ 英文 slug 双向映射
const categoryZhToSlug: Record<string, string> = {
  '技术研习': 'tech-study', '踩坑复盘': 'pitfall-review',
  '项目实战': 'project-practice', '成长随笔': 'growth-essay', '资源分享': 'resource-sharing'
}
const categorySlugToZh: Record<string, string> = {
  'tech-study': '技术研习', 'pitfall-review': '踩坑复盘',
  'project-practice': '项目实战', 'growth-essay': '成长随笔', 'resource-sharing': '资源分享'
}

// 二级分类选项映射
const subCategoryMap: Record<string, SelectOption[]> = {
  'tech-study': [
    { label: '前端', value: 'frontend' },
    { label: '后端', value: 'backend' },
    { label: 'AI', value: 'ai' },
    { label: 'LLM', value: 'llm' },
    { label: 'Git', value: 'git' },
    { label: 'Hexo', value: 'hexo' }
  ],
  'pitfall-review': [
    { label: 'Docker', value: 'docker' },
    { label: '环境配置', value: 'env' },
    { label: '部署', value: 'deploy' }
  ],
  'project-practice': [
    { label: '博客', value: 'blog' },
    { label: '工具', value: 'tool' }
  ],
  'growth-essay': [
    { label: '年度总结', value: 'annual' },
    { label: '求职', value: 'career' },
    { label: '读书笔记', value: 'read' },
    { label: '学习方法', value: 'learn' }
  ],
  'resource-sharing': [
    { label: 'Claude', value: 'claude' },
    { label: '工具推荐', value: 'tool' }
  ]
}

// 解析当前一级分类的英文 slug（兼容中文名和英文 slug）
const primaryCategorySlug = computed(() => {
  const raw = frontMatter.value.categories?.[0] || ''
  return categoryZhToSlug[raw] || raw
})

// 解析当前二级分类的英文 slug（兼容中文名和英文 slug）
const subCategorySlugToZh = computed(() => {
  const map: Record<string, string> = {}
  const options = subCategoryMap[primaryCategorySlug.value] || []
  options.forEach(opt => { map[opt.value] = opt.label as string })
  return map
})

// 当前二级分类选项
const subCategoryOptions = computed(() => {
  return subCategoryMap[primaryCategorySlug.value] || []
})

// 展开设置面板
const showSettings = ref(false)

// 标签编辑对话框
const showTagEditor = ref(false)
const editingTags = ref<string[]>([])

// ByteMD 插件
const plugins = [
  gfm(),
  highlight(),
  frontmatter()
]

// AI 助手相关状态
const aiAssistantRef = ref<InstanceType<typeof AIAssistant> | null>(null)
const selectedText = ref('')
const selectionStart = ref(0)
const selectionEnd = ref(0)

// 是否有修改
const hasChanges = computed(() => {
  return articleContent.value !== originalContent.value
})

// 加载文章
async function loadArticle() {
  const path = route.query.file as string
  if (!path) {
    message.error('缺少文章路径参数')
    return
  }

  articlePath.value = path
  isLoading.value = true

  try {
    const detail = await api.getPost(path) as PostDetail
    articleContent.value = detail.content || ''
    originalContent.value = detail.content || ''

    if (detail.frontMatter) {
      frontMatter.value = { ...detail.frontMatter }
    }

    // 解析内容
    const parsed = parseFrontMatter(articleContent.value)
    frontMatter.value = parsed.frontMatter

    // 扁平化嵌套分类（YAML 解析 categories: - [一级, 二级] 得到 [[一级, 二级]]，需展平为 [一级, 二级]）
    if (Array.isArray(frontMatter.value.categories?.[0])) {
      frontMatter.value.categories = frontMatter.value.categories.flat() as string[]
    }

    bodyContent.value = parsed.body

    // 设置日期时间戳
    if (frontMatter.value.date) {
      const dateStr = frontMatter.value.date.replace(' ', 'T')
      dateTimestamp.value = new Date(dateStr).getTime()
    }
  } catch (error) {
    console.error('加载文章失败:', error)
    message.error('加载文章失败')
  } finally {
    isLoading.value = false
  }
}

// 保存文章
async function saveArticle() {
  if (!articlePath.value) {
    message.error('文章路径不存在')
    return
  }

  // 验证 Front Matter
  const validation = validateFrontMatter(frontMatter.value)
  if (!validation.valid) {
    message.error(validation.errors[0])
    return
  }

  isSaving.value = true
  saveStatus.value = 'saving'

  try {
    // 构建完整内容
    const content = buildMarkdown(frontMatter.value, bodyContent.value)

    // 调用 API 更新
    await api.updatePost(articlePath.value, content)

    articleContent.value = content
    originalContent.value = content
    saveStatus.value = 'saved'

    message.success('保存成功')

    // 3秒后重置状态
    setTimeout(() => {
      if (saveStatus.value === 'saved') {
        saveStatus.value = 'idle'
      }
    }, 3000)
  } catch (error) {
    console.error('保存失败:', error)
    message.error('保存失败')
    saveStatus.value = 'idle'
  } finally {
    isSaving.value = false
  }
}

// 发布文章
async function publishArticle() {
  dialog.warning({
    title: '确认发布',
    content: '发布后将触发博客部署，确定要发布吗？',
    positiveText: '发布',
    negativeText: '取消',
    onPositiveClick: async () => {
      // 设置状态为已发布
      frontMatter.value.status = 'published'

      // 先保存
      await saveArticle()

      // 触发部署
      try {
        await api.deploy(`发布文章: ${frontMatter.value.title}`)
        message.success('发布成功，博客正在部署中...')
      } catch (error) {
        console.error('部署失败:', error)
        message.error('部署失败，请手动部署')
      }
    }
  })
}

// 返回上一页
function goBack() {
  if (hasChanges.value) {
    dialog.warning({
      title: '未保存的更改',
      content: '有未保存的更改，确定要离开吗？',
      positiveText: '离开',
      negativeText: '取消',
      onPositiveClick: () => {
        // 如果有浏览器历史则返回，否则跳转到仪表盘
        if (window.history.length > 1) {
          router.back()
        } else {
          router.push('/')
        }
      }
    })
  } else {
    if (window.history.length > 1) {
      router.back()
    } else {
      router.push('/')
    }
  }
}

// 编辑器内容变化
function handleEditorChange(value: string) {
  articleContent.value = value
  resetAutoSaveTimer()

  // 解析 Front Matter 和 Body
  try {
    const parsed = parseFrontMatter(value)
    frontMatter.value = { ...parsed.frontMatter }

    // 扁平化嵌套分类
    if (Array.isArray(frontMatter.value.categories?.[0])) {
      frontMatter.value.categories = frontMatter.value.categories.flat() as string[]
    }

    bodyContent.value = parsed.body
  } catch (error) {
    console.error('解析失败:', error)
  }
}

// 处理编辑器文本选中
function handleEditorSelection() {
  // 获取编辑器的 textarea 元素
  const editorEl = document.querySelector('.bytemd-editor textarea') as HTMLTextAreaElement
  if (!editorEl) return
  
  const start = editorEl.selectionStart
  const end = editorEl.selectionEnd
  
  if (start !== end) {
    selectedText.value = articleContent.value.substring(start, end)
    selectionStart.value = start
    selectionEnd.value = end
  } else {
    selectedText.value = ''
    selectionStart.value = start
    selectionEnd.value = start
  }
}

// 处理 AI 助手插入文本
function handleInsertText(text: string) {
  const editorEl = document.querySelector('.bytemd-editor textarea') as HTMLTextAreaElement
  if (!editorEl) {
    message.error('无法获取编辑器元素')
    return
  }
  
  // 如果有选中文本，替换；否则插入到光标位置
  if (selectedText.value) {
    // 替换选中的文本
    const before = articleContent.value.substring(0, selectionStart.value)
    const after = articleContent.value.substring(selectionEnd.value)
    articleContent.value = before + text + after
    
    // 更新光标位置
    const newPosition = selectionStart.value + text.length
    editorEl.setSelectionRange(newPosition, newPosition)
    
    // 清空选中状态
    selectedText.value = ''
  } else {
    // 插入到光标位置
    const position = selectionStart.value
    const before = articleContent.value.substring(0, position)
    const after = articleContent.value.substring(position)
    articleContent.value = before + text + after
    
    // 更新光标位置
    const newPosition = position + text.length
    editorEl.setSelectionRange(newPosition, newPosition)
  }
  
  // 触发编辑器更新
  editorEl.value = articleContent.value
  editorEl.dispatchEvent(new Event('input'))
  
  // 解析更新后的内容
  try {
    const parsed = parseFrontMatter(articleContent.value)
    frontMatter.value = { ...parsed.frontMatter }
    bodyContent.value = parsed.body
  } catch (error) {
    console.error('解析失败:', error)
  }
  
  message.success('内容已插入')
}

// 标题变化
function handleTitleChange(value: string) {
  frontMatter.value.title = value
  updateContent()
}

// 状态变化
function handleStatusChange(value: 'draft' | 'wip' | 'published') {
  frontMatter.value.status = value
  updateContent()
}

// 一级分类变化（select 传入英文 slug，需转为中文存入 front matter）
function handleCategoryChange(value: string) {
  frontMatter.value.categories = [categorySlugToZh[value] || value]
  updateContent()
}

// 二级分类变化（select 传入英文 slug，需转为中文存入 front matter）
function handleSubCategoryChange(value: string) {
  const mainZh = frontMatter.value.categories?.[0] || ''
  const subZh = subCategorySlugToZh.value[value] || value
  frontMatter.value.categories = [mainZh, subZh]
  updateContent()
}

// 更新内容
function updateContent() {
  const content = buildMarkdown(frontMatter.value, bodyContent.value)
  articleContent.value = content
}

// 日期变化
function handleDateChange(timestamp: number) {
  const date = new Date(timestamp)
  const dateStr = date.toISOString().replace('T', ' ').slice(0, 19)
  frontMatter.value.date = dateStr
  updateContent()
}

// 打开标签编辑器
function openTagEditor() {
  editingTags.value = [...(frontMatter.value.tags || [])]
  showTagEditor.value = true
}

// 保存标签
function saveTags() {
  frontMatter.value.tags = [...editingTags.value]
  showTagEditor.value = false
  updateContent()
}

// 添加标签
function addTag() {
  editingTags.value.push('')
}

// 删除标签
function removeTag(index: number) {
  editingTags.value.splice(index, 1)
}

// 自动保存
let autoSaveTimer: number | null = null

function resetAutoSaveTimer() {
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer)
  }
  autoSaveTimer = window.setTimeout(() => {
    if (hasChanges.value && !isSaving.value) {
      saveArticle()
    }
  }, 300000) // 5分钟
}

function stopAutoSave() {
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer)
    autoSaveTimer = null
  }
}

// 监听路由变化
watch(() => route.query.file, () => {
  if (route.query.file) {
    loadArticle()
  }
})

// 生命周期
onMounted(() => {
  loadArticle()
  
  // 监听编辑器选中事件
  const editorEl = document.querySelector('.bytemd-editor textarea')
  if (editorEl) {
    editorEl.addEventListener('select', handleEditorSelection)
    editorEl.addEventListener('mouseup', handleEditorSelection)
    editorEl.addEventListener('keyup', handleEditorSelection)
  }
})

onUnmounted(() => {
  stopAutoSave()
  
  // 移除编辑器选中事件监听
  const editorEl = document.querySelector('.bytemd-editor textarea')
  if (editorEl) {
    editorEl.removeEventListener('select', handleEditorSelection)
    editorEl.removeEventListener('mouseup', handleEditorSelection)
    editorEl.removeEventListener('keyup', handleEditorSelection)
  }
})
</script>

<template>
  <div class="editor-container">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <n-button quaternary @click="goBack">
          <template #icon>
            <n-icon>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M7.82843 10.9999H20V12.9999H7.82843L13.1924 18.3638L11.7782 19.778L4 11.9999L11.7782 4.22168L13.1924 5.63589L7.82843 10.9999Z"/>
              </svg>
            </n-icon>
          </template>
          返回
        </n-button>
        <n-text v-if="saveStatus === 'saving'" type="warning" style="margin-left: 16px;">
          自动保存中...
        </n-text>
        <n-text v-else-if="saveStatus === 'saved'" type="success" style="margin-left: 16px;">
          已保存
        </n-text>
      </div>
      <div class="toolbar-right">
        <n-select
          v-model:value="frontMatter.status"
          :options="statusOptions"
          style="width: 120px; margin-right: 12px;"
          @update:value="handleStatusChange"
        />
        <n-button
          :loading="isSaving"
          :disabled="!hasChanges"
          @click="saveArticle"
          style="margin-right: 8px;"
        >
          保存草稿
        </n-button>
        <n-button
          type="primary"
          :loading="isSaving"
          :disabled="frontMatter.status === 'published' && !hasChanges"
          @click="publishArticle"
        >
          发布
        </n-button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content" v-if="!isLoading">
      <!-- 标题区 -->
      <div class="title-section">
        <n-input
          v-model:value="frontMatter.title"
          placeholder="请输入文章标题"
          :input-props="{ style: 'font-size: 28px; font-weight: bold;' }"
          @update:value="handleTitleChange"
        />
      </div>

      <!-- 元数据标签行 -->
      <div class="metadata-tags">
        <n-space>
          <n-tag
            v-if="frontMatter.categories?.[0]"
            type="primary"
            closable
            @close="frontMatter.categories = []"
          >
            {{ categoryOptions.find(o => o.value === frontMatter.categories?.[0])?.label || frontMatter.categories[0] }}
          </n-tag>
          <n-tag
            v-if="frontMatter.categories?.[1]"
            type="info"
            closable
            @close="frontMatter.categories = [frontMatter.categories[0]]"
          >
            {{ subCategoryOptions.find(o => o.value === frontMatter.categories?.[1])?.label || frontMatter.categories[1] }}
          </n-tag>
          <n-tag
            v-for="(tag, index) in frontMatter.tags"
            :key="index"
            type="success"
            closable
            @close="frontMatter.tags?.splice(index, 1); updateContent()"
          >
            {{ tag }}
          </n-tag>
          <n-button size="small" @click="showSettings = !showSettings">
            {{ showSettings ? '收起设置' : '展开全部设置' }}
          </n-button>
        </n-space>
      </div>

      <!-- Front Matter 完整设置面板 -->
      <n-card v-if="showSettings" title="文章设置" class="settings-card">
        <n-form label-placement="left" label-width="100">
          <n-form-item label="创建日期">
            <n-date-picker
              v-model:value="dateTimestamp"
              type="datetime"
              format="yyyy-MM-dd HH:mm:ss"
              style="width: 240px;"
              @update:value="handleDateChange"
            />
          </n-form-item>
          <n-form-item label="更新日期">
            <n-date-picker
              :value="frontMatter.updated ? new Date(frontMatter.updated.replace(' ', 'T')).getTime() : null"
              type="datetime"
              format="yyyy-MM-dd HH:mm:ss"
              style="width: 240px;"
              clearable
              @update:value="(v: number | null) => {
                if (v) {
                  const d = new Date(v)
                  frontMatter.updated = d.toISOString().replace('T', ' ').slice(0, 19)
                } else {
                  frontMatter.updated = undefined
                }
                updateContent()
              }"
            />
          </n-form-item>
          <n-form-item label="一级分类">
            <n-select
              :value="primaryCategorySlug || null"
              :options="categoryOptions"
              style="width: 200px;"
              @update:value="handleCategoryChange"
            />
          </n-form-item>
          <n-form-item label="二级分类">
            <n-select
              :value="frontMatter.categories?.[1] ? (subCategoryOptions.find(o => o.label === frontMatter.categories[1])?.value ?? frontMatter.categories[1]) : null"
              :options="subCategoryOptions"
              style="width: 200px;"
              clearable
              @update:value="handleSubCategoryChange"
            />
          </n-form-item>
          <n-form-item label="标签">
            <n-button size="small" @click="openTagEditor">
              编辑标签 ({{ frontMatter.tags?.length || 0 }})
            </n-button>
          </n-form-item>
          <n-form-item label="文章描述">
            <n-input
              v-model:value="frontMatter.description"
              type="textarea"
              placeholder="请输入文章描述（100-200字）"
              :rows="3"
              @update:value="updateContent"
            />
          </n-form-item>
          <n-form-item label="布局">
            <n-input
              :value="frontMatter.layout ?? ''"
              placeholder="post"
              style="width: 200px;"
              @update:value="(v: string) => { frontMatter.layout = v || undefined; updateContent() }"
            />
          </n-form-item>
          <n-form-item label="评论">
            <n-select
              :value="frontMatter.comments === false ? false : true"
              :options="[{ label: '开启', value: true }, { label: '关闭', value: false }]"
              style="width: 120px;"
              @update:value="(v: boolean) => { frontMatter.comments = v; updateContent() }"
            />
          </n-form-item>
          <n-form-item label="永久链接">
            <n-input
              :value="frontMatter.permalink ?? ''"
              placeholder="自定义永久链接"
              style="width: 300px;"
              @update:value="(v: string) => { frontMatter.permalink = v || undefined; updateContent() }"
            />
          </n-form-item>
          <n-form-item label="摘要">
            <n-input
              :value="frontMatter.excerpt ?? ''"
              type="textarea"
              placeholder="文章摘要"
              :rows="2"
              @update:value="(v: string) => { frontMatter.excerpt = v || undefined; updateContent() }"
            />
          </n-form-item>
          <n-form-item label="是否发布">
            <n-select
              :value="frontMatter.published === false ? false : true"
              :options="[{ label: '是', value: true }, { label: '否', value: false }]"
              style="width: 120px;"
              @update:value="(v: boolean) => { frontMatter.published = v; updateContent() }"
            />
          </n-form-item>
          <n-form-item label="语言">
            <n-input
              :value="frontMatter.lang ?? ''"
              placeholder="zh-CN"
              style="width: 200px;"
              @update:value="(v: string) => { frontMatter.lang = v || undefined; updateContent() }"
            />
          </n-form-item>
          <n-form-item label="封面图">
            <n-input
              :value="frontMatter.cover ?? ''"
              placeholder="/img/covers/xxx.svg"
              style="width: 300px;"
              @update:value="(v: string) => { frontMatter.cover = v || undefined; updateContent() }"
            />
          </n-form-item>
          <n-form-item label="置顶权重">
            <n-input-number
              :value="frontMatter.sticky ?? null"
              placeholder="数字越大越靠前"
              :min="0"
              style="width: 200px;"
              @update:value="(v: number | null) => { frontMatter.sticky = v ?? undefined; updateContent() }"
            />
          </n-form-item>
          <n-form-item label="自定义链接">
            <n-input
              :value="frontMatter.slug ?? ''"
              placeholder="自定义 URL slug"
              style="width: 300px;"
              @update:value="(v: string) => { frontMatter.slug = v || undefined; updateContent() }"
            />
          </n-form-item>
          <n-form-item label="系列名称">
            <n-input
              :value="frontMatter.series ?? ''"
              placeholder="系列文章名称"
              style="width: 300px;"
              @update:value="(v: string) => { frontMatter.series = v || undefined; updateContent() }"
            />
          </n-form-item>
          <n-form-item v-if="frontMatter.series" label="系列顺序">
            <n-input-number
              :value="frontMatter.series_order ?? null"
              placeholder="系列中的顺序"
              :min="1"
              style="width: 200px;"
              @update:value="(v: number | null) => { frontMatter.series_order = v ?? undefined; updateContent() }"
            />
          </n-form-item>
          <n-form-item label="文章状态">
            <n-select
              v-model:value="frontMatter.status"
              :options="statusOptions"
              style="width: 200px;"
              @update:value="handleStatusChange"
            />
          </n-form-item>
        </n-form>
      </n-card>

      <!-- ByteMD 编辑器 -->
      <div class="editor-wrapper">
        <ByteMDEditor
          :value="articleContent"
          :plugins="plugins"
          @change="handleEditorChange"
        />
      </div>
    </div>

    <!-- 加载中 -->
    <div v-else class="loading">
      <n-text>加载中...</n-text>
    </div>

    <!-- 标签编辑对话框 -->
    <n-modal
      v-model:show="showTagEditor"
      preset="card"
      title="编辑标签"
      style="width: 500px;"
    >
      <n-space vertical>
        <div v-for="(tag, index) in editingTags" :key="index" style="display: flex; gap: 8px; align-items: center;">
          <n-input
            v-model:value="editingTags[index]"
            placeholder="标签名称"
            style="flex: 1;"
          />
          <n-button size="small" type="error" @click="removeTag(index)">
            删除
          </n-button>
        </div>
        <n-button size="small" @click="addTag">
          添加标签
        </n-button>
      </n-space>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showTagEditor = false">取消</n-button>
          <n-button type="primary" @click="saveTags">保存</n-button>
        </n-space>
      </template>
    </n-modal>
    
    <!-- AI 写作助手 -->
    <AIAssistant
      ref="aiAssistantRef"
      :editor-content="articleContent"
      :selected-text="selectedText"
      :cursor-position="selectionStart"
      @insert-text="handleInsertText"
    />
  </div>
</template>

<style scoped>
.editor-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  overflow: hidden;
}

.toolbar {
  display: flex;
  flex-shrink: 0;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid #e0e0e0;
  background: #fafafa;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
}

.main-content {
  flex: 1;
  height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.title-section {
  flex-shrink: 0;
  padding: 20px 24px 12px;
  border-bottom: 1px solid #f0f0f0;
}

.metadata-tags {
  flex-shrink: 0;
  padding: 12px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.settings-card {
  flex-shrink: 0;
  margin: 16px 24px;
  max-height: 400px;
  overflow-y: auto;
}

.editor-wrapper {
  flex: 1;
  min-height: 0;
  position: relative;
}

.editor-wrapper :deep(.bytemd) {
  position: absolute !important;
  inset: 0;
  height: auto !important;
  max-height: none !important;
  border: none;
}

.editor-wrapper :deep(.bytemd-body) {
  height: calc(100% - 58px) !important;
  max-height: none !important;
  overflow: hidden;
}

.editor-wrapper :deep(.bytemd-editor) {
  height: 100% !important;
  max-height: none !important;
  overflow: hidden;
}

.editor-wrapper :deep(.bytemd-editor .CodeMirror) {
  height: 100% !important;
  max-height: none !important;
}

.editor-wrapper :deep(.bytemd-preview) {
  height: 100% !important;
  max-height: none !important;
  overflow-y: auto !important;
}

.loading {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>