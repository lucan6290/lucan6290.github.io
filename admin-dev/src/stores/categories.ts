/**
 * 分类管理 Store
 * 管理自定义分类，持久化到 localStorage
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * 分类接口
 */
export interface Category {
  /** 一级分类名称 */
  name: string
  /** 一级分类英文名（用于 URL） */
  slug: string
  /** 二级分类列表 */
  subCategories: SubCategory[]
}

/**
 * 二级分类接口
 */
export interface SubCategory {
  /** 二级分类名称 */
  name: string
  /** 二级分类英文名（用于 URL） */
  slug: string
  /** 是否为自定义分类 */
  isCustom: boolean
  /** 所属一级分类 slug（仅自定义分类需要） */
  parentSlug?: string
}

/**
 * 默认一级分类（从 _config.yml 中提取）
 */
const DEFAULT_CATEGORIES: Category[] = [
  {
    name: '技术研习',
    slug: 'tech-study',
    subCategories: [
      { name: '入门笔记', slug: 'beginner-notes', isCustom: false },
      { name: '进阶教程', slug: 'advanced-tutorial', isCustom: false },
      { name: '原理探究', slug: 'principle-deep-dive', isCustom: false },
      { name: '源码解读', slug: 'source-code-reading', isCustom: false },
      { name: '前沿追踪', slug: 'frontier-tracking', isCustom: false },
      { name: 'AI 探索', slug: 'ai-exploration', isCustom: false },
      { name: '系列专题', slug: 'series', isCustom: false }
    ]
  },
  {
    name: '踩坑复盘',
    slug: 'pitfall-review',
    subCategories: [
      { name: '环境配置', slug: 'env-config', isCustom: false },
      { name: '代码调试', slug: 'code-debug', isCustom: false },
      { name: '工程问题', slug: 'engineering', isCustom: false },
      { name: '部署运维', slug: 'deploy-ops', isCustom: false },
      { name: '数据问题', slug: 'data-issue', isCustom: false },
      { name: '工具问题', slug: 'tool-issue', isCustom: false }
    ]
  },
  {
    name: '项目实战',
    slug: 'project-practice',
    subCategories: [
      { name: '项目介绍', slug: 'project-intro', isCustom: false },
      { name: '架构设计', slug: 'architecture', isCustom: false },
      { name: '开发日志', slug: 'dev-log', isCustom: false },
      { name: '功能实现', slug: 'feature-impl', isCustom: false },
      { name: '性能优化', slug: 'perf-optimize', isCustom: false },
      { name: '项目总结', slug: 'project-summary', isCustom: false },
      { name: '开源分享', slug: 'open-source', isCustom: false }
    ]
  },
  {
    name: '成长随笔',
    slug: 'growth-essay',
    subCategories: [
      { name: '求职之路', slug: 'job-hunting', isCustom: false },
      { name: '简历优化', slug: 'resume', isCustom: false },
      { name: '面试真题', slug: 'interview', isCustom: false },
      { name: 'offer选择', slug: 'offer-choice', isCustom: false },
      { name: '学习方法', slug: 'learning-method', isCustom: false },
      { name: '读书笔记', slug: 'reading-note', isCustom: false },
      { name: '日常感悟', slug: 'daily-thoughts', isCustom: false },
      { name: '短思考', slug: 'short-think', isCustom: false },
      { name: '年度总结', slug: 'annual-summary', isCustom: false },
      { name: '博客建设', slug: 'blog-building', isCustom: false },
      { name: 'AI 思考', slug: 'ai-thinking', isCustom: false }
    ]
  },
  {
    name: '资源分享',
    slug: 'resource-sharing',
    subCategories: [
      { name: '工具推荐', slug: 'tool-recommend', isCustom: false },
      { name: '学习资源', slug: 'learning-resource', isCustom: false },
      { name: '代码片段', slug: 'code-snippet', isCustom: false },
      { name: '模板分享', slug: 'template-share', isCustom: false },
      { name: '文档翻译', slug: 'doc-translation', isCustom: false },
      { name: 'cheatsheet', slug: 'cheatsheet', isCustom: false }
    ]
  }
]

const STORAGE_KEY = 'blog-admin-custom-categories'

/**
 * 从 localStorage 加载自定义分类
 */
function loadCustomCategoriesFromStorage(): SubCategory[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored) as SubCategory[]
    }
  } catch (error) {
    console.warn('从 localStorage 加载自定义分类失败:', error)
  }
  return []
}

/**
 * 保存自定义分类到 localStorage
 */
function saveCustomCategoriesToStorage(categories: SubCategory[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(categories))
  } catch (error) {
    console.warn('保存自定义分类到 localStorage 失败:', error)
  }
}

/**
 * 生成 slug（将中文转换为拼音或使用英文）
 * 这里简化处理，实际项目中可能需要使用拼音库
 */
function generateSlug(name: string): string {
  // 简化处理：移除特殊字符，转小写，空格转连字符
  return name
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^\w\u4e00-\u9fa5-]/g, '')
}

export const useCategoriesStore = defineStore('categories', () => {
  // State
  const customCategories = ref<SubCategory[]>(loadCustomCategoriesFromStorage())

  // Getters
  /**
   * 获取所有分类（包含默认分类和自定义分类）
   */
  const allCategories = computed(() => {
    return DEFAULT_CATEGORIES.map(category => {
      // 找到属于该一级分类的自定义二级分类
      const customSubs = customCategories.value.filter(
        sub => sub.parentSlug === category.slug
      )

      return {
        ...category,
        subCategories: [...category.subCategories, ...customSubs]
      }
    })
  })

  /**
   * 获取一级分类列表
   */
  const primaryCategories = computed(() => {
    return DEFAULT_CATEGORIES.map(c => ({
      label: c.name,
      value: c.slug
    }))
  })

  // Actions

  /**
   * 添加自定义二级分类
   * @param parentSlug 一级分类 slug
   * @param name 二级分类名称
   */
  function addCustomCategory(parentSlug: string, name: string): boolean {
    // 检查是否已存在（同一级分类下）
    const exists = customCategories.value.some(
      c => c.name === name && c.parentSlug === parentSlug
    )
    if (exists) {
      console.warn('分类已存在:', name)
      return false
    }

    const newCategory: SubCategory = {
      name,
      slug: generateSlug(name),
      isCustom: true,
      parentSlug
    }

    customCategories.value.push(newCategory)
    saveCustomCategoriesToStorage(customCategories.value)
    console.log('添加自定义分类:', name, '到一级分类:', parentSlug)
    return true
  }

  /**
   * 删除自定义分类
   * @param name 分类名称
   */
  function removeCustomCategory(name: string): void {
    const index = customCategories.value.findIndex(c => c.name === name)
    if (index > -1) {
      customCategories.value.splice(index, 1)
      saveCustomCategoriesToStorage(customCategories.value)
      console.log('删除自定义分类:', name)
    }
  }

  /**
   * 获取指定一级分类下的所有二级分类
   * @param parentSlug 一级分类 slug
   */
  function getSubCategories(parentSlug: string): SubCategory[] {
    const category = DEFAULT_CATEGORIES.find(c => c.slug === parentSlug)
    if (!category) return []

    // 合并默认二级分类和该一级分类下的自定义二级分类
    const customSubs = customCategories.value.filter(
      sub => sub.parentSlug === parentSlug
    )
    return [...category.subCategories, ...customSubs]
  }

  /**
   * 重置自定义分类
   */
  function resetCustomCategories(): void {
    customCategories.value = []
    saveCustomCategoriesToStorage(customCategories.value)
    console.log('自定义分类已重置')
  }

  return {
    // State
    customCategories,

    // Getters
    allCategories,
    primaryCategories,

    // Actions
    addCustomCategory,
    removeCustomCategory,
    getSubCategories,
    resetCustomCategories
  }
})