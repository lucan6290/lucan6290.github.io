import { ref } from 'vue'
import { defineStore } from 'pinia'
import { getAPI } from '@/api'
import type {
  AIModelPayload,
  AIWritingError,
  KnowledgeQAResponse
} from '@/types/ai-writing'

type KnowledgeIndexStatus = 'unknown' | 'missing' | 'ready' | 'stale' | 'rebuilding' | 'error'

function createError(code: string, title: string, message: string, retryable = true): AIWritingError {
  return { code, title, message, retryable }
}

export const useKnowledgeIndexStore = defineStore('knowledgeIndex', () => {
  const indexStatus = ref<KnowledgeIndexStatus>('unknown')
  const scannedAt = ref<string | null>(null)
  const articleCount = ref(0)
  const draftCount = ref(0)
  const failedFiles = ref<string[]>([])
  const isScanning = ref(false)
  const isAsking = ref(false)
  const question = ref('')
  const forceRescan = ref(false)
  const answer = ref<KnowledgeQAResponse | null>(null)
  const history = ref<KnowledgeQAResponse[]>([])
  const error = ref<AIWritingError | null>(null)

  async function loadIndex(): Promise<void> {
    const api = getAPI()
    if (!api.getArticleIndex) {
      indexStatus.value = 'missing'
      error.value = createError('INDEX_API_MISSING', '索引接口不可用', '当前后端尚未提供文章索引接口。')
      return
    }

    try {
      const result = await api.getArticleIndex()
      scannedAt.value = result.scannedAt
      articleCount.value = result.articleCount
      draftCount.value = result.draftCount
      failedFiles.value = result.failedFiles || []
      indexStatus.value = result.indexStatus === 'failed' ? 'error' : 'ready'
      error.value = null
    } catch (err) {
      indexStatus.value = 'missing'
      error.value = createError('INDEX_LOAD_FAILED', '索引读取失败', err instanceof Error ? err.message : '请尝试重新扫描。')
    }
  }

  async function scanIndex(): Promise<void> {
    const api = getAPI()
    if (!api.scanArticleIndex) {
      error.value = createError('INDEX_SCAN_API_MISSING', '扫描接口不可用', '当前后端尚未提供文章扫描接口。')
      return
    }

    isScanning.value = true
    indexStatus.value = 'rebuilding'
    try {
      const result = await api.scanArticleIndex()
      scannedAt.value = result.scannedAt
      articleCount.value = result.articleCount
      draftCount.value = result.draftCount
      failedFiles.value = result.failedFiles || []
      indexStatus.value = result.indexStatus === 'failed' ? 'error' : 'ready'
      error.value = null
    } catch (err) {
      indexStatus.value = 'error'
      error.value = createError('INDEX_SCAN_FAILED', '索引扫描失败', err instanceof Error ? err.message : '请检查本地博客目录配置。')
    } finally {
      isScanning.value = false
    }
  }

  async function askKnowledge(model?: AIModelPayload): Promise<void> {
    if (!question.value.trim()) return

    const api = getAPI()
    if (!api.knowledgeQA) {
      error.value = createError('KNOWLEDGE_API_MISSING', '知识库问答接口不可用', '当前后端尚未提供知识库问答接口。')
      return
    }

    isAsking.value = true
    try {
      const result = await api.knowledgeQA({
        question: question.value,
        forceRescan: forceRescan.value,
        includeDrafts: true,
        model
      })
      answer.value = result
      history.value.unshift(result)
      error.value = null
    } catch (err) {
      error.value = createError('KNOWLEDGE_QA_FAILED', '知识库问答失败', err instanceof Error ? err.message : '请稍后重试。')
    } finally {
      isAsking.value = false
    }
  }

  return {
    indexStatus,
    scannedAt,
    articleCount,
    draftCount,
    failedFiles,
    isScanning,
    isAsking,
    question,
    forceRescan,
    answer,
    history,
    error,
    loadIndex,
    scanIndex,
    askKnowledge
  }
})
