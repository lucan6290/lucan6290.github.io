/**
 * 分类注册表 Store
 * 统一管理前端显示名、Front Matter 分类名、文章文件名前缀和目录 slug。
 */
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { getAPI } from '@/api'
import type { CategoryRegistryChild, CategoryRegistryItem } from '@/types/ai-writing'

export type { CategoryRegistryChild, CategoryRegistryItem }

export interface Category {
  type: string
  name: string
  slug: string
  prefix: string
  cover: string
  enabled: boolean
  sortOrder: number
  subCategories: SubCategory[]
}

export interface SubCategory {
  name: string
  slug: string
  prefix: string
  enabled: boolean
  sortOrder: number
  isCustom: boolean
  parentSlug?: string
}

const FALLBACK_REGISTRY: CategoryRegistryItem[] = []

function sortRegistry(registry: CategoryRegistryItem[]): CategoryRegistryItem[] {
  return [...registry]
    .sort((a, b) => (a.sort_order || 9999) - (b.sort_order || 9999))
    .map((item) => ({
      ...item,
      children: [...(item.children || [])].sort(
        (a, b) => (a.sort_order || 9999) - (b.sort_order || 9999)
      )
    }))
}

function withLegacyFields(item: CategoryRegistryItem): CategoryRegistryItem {
  return {
    ...item,
    type: item.type || 'docs',
    prefix1: item.note_prefix1,
    primaryName: item.frontend_name1,
    primarySlug: item.category_slug,
    dir: item.category_slug,
    children: item.children || []
  }
}

function normalizeRegistry(registry: CategoryRegistryItem[]): CategoryRegistryItem[] {
  return sortRegistry(
    registry.map((item, index) =>
      withLegacyFields({
        ...item,
        frontend_name1: item.frontend_name1 || item.primaryName,
        category_slug: item.category_slug || item.primarySlug || item.dir,
        note_prefix1: item.note_prefix1 || item.prefix1,
        cover: item.cover || '',
        sort_order: item.sort_order || (index + 1) * 10,
        enabled: item.enabled !== false,
        children: (item.children || []).map((child, childIndex) => ({
          ...child,
          frontend_name2: child.frontend_name2,
          note_prefix2: child.note_prefix2,
          sort_order: child.sort_order || (childIndex + 1) * 10,
          enabled: child.enabled !== false
        }))
      })
    )
  )
}

export const useCategoriesStore = defineStore('categories', () => {
  const registry = ref<CategoryRegistryItem[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const loaded = ref(false)

  const allCategories = computed<Category[]>(() =>
    registry.value.map((category) => ({
      type: category.type || 'docs',
      name: category.frontend_name1,
      slug: category.category_slug,
      prefix: category.note_prefix1,
      cover: category.cover,
      enabled: category.enabled,
      sortOrder: category.sort_order,
      subCategories: category.children.map((sub) => ({
        name: sub.frontend_name2,
        slug: sub.note_prefix2,
        prefix: sub.note_prefix2,
        enabled: sub.enabled,
        sortOrder: sub.sort_order,
        isCustom: true,
        parentSlug: category.category_slug
      }))
    }))
  )

  const customCategories = computed<SubCategory[]>(() =>
    allCategories.value.flatMap((category) => category.subCategories)
  )

  const primaryCategories = computed(() =>
    registry.value.map((category) => ({
      label: `${category.frontend_name1} (${category.note_prefix1})`,
      value: category.note_prefix1
    }))
  )

  const enabledPrimaryCategories = computed(() =>
    registry.value
      .filter((category) => category.enabled)
      .map((category) => ({
        label: `${category.frontend_name1} (${category.note_prefix1})`,
        value: category.note_prefix1
      }))
  )

  async function fetchRegistry(force = false): Promise<CategoryRegistryItem[]> {
    if (loaded.value && !force) return registry.value
    isLoading.value = true
    error.value = null

    try {
      const api = getAPI()
      const result = api.getCategoryRegistry
        ? await api.getCategoryRegistry()
        : FALLBACK_REGISTRY
      registry.value = normalizeRegistry(result as CategoryRegistryItem[])
      loaded.value = true
      return registry.value
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载分类注册表失败'
      if (!registry.value.length) registry.value = normalizeRegistry(FALLBACK_REGISTRY)
      return registry.value
    } finally {
      isLoading.value = false
    }
  }

  async function saveRegistry(nextRegistry = registry.value): Promise<CategoryRegistryItem[]> {
    const normalized = normalizeRegistry(nextRegistry)
    const api = getAPI()
    if (!api.updateCategoryRegistry) {
      registry.value = normalized
      return registry.value
    }
    const saved = await api.updateCategoryRegistry(normalized)
    registry.value = normalizeRegistry(saved as CategoryRegistryItem[])
    loaded.value = true
    return registry.value
  }

  function getPrimaryByPrefix(notePrefix1: string | null | undefined): CategoryRegistryItem | undefined {
    return registry.value.find((category) => category.note_prefix1 === notePrefix1)
  }

  function getPrimaryBySlug(categorySlug: string | null | undefined): CategoryRegistryItem | undefined {
    return registry.value.find((category) => category.category_slug === categorySlug)
  }

  function getSecondaryByPrefix(
    notePrefix1: string | null | undefined,
    notePrefix2: string | null | undefined
  ): CategoryRegistryChild | undefined {
    return getPrimaryByPrefix(notePrefix1)?.children.find((child) => child.note_prefix2 === notePrefix2)
  }

  function getSubCategories(notePrefixOrSlug: string): SubCategory[] {
    const category = getPrimaryByPrefix(notePrefixOrSlug) || getPrimaryBySlug(notePrefixOrSlug)
    if (!category) return []
    return category.children.map((sub) => ({
      name: sub.frontend_name2,
      slug: sub.note_prefix2,
      prefix: sub.note_prefix2,
      enabled: sub.enabled,
      sortOrder: sub.sort_order,
      isCustom: true,
      parentSlug: category.category_slug
    }))
  }

  async function addPrimaryCategory(
    category: Pick<CategoryRegistryItem, 'frontend_name1' | 'category_slug' | 'note_prefix1'> &
      Partial<CategoryRegistryItem>
  ): Promise<boolean> {
    const next = normalizeRegistry(registry.value)
    const exists = next.some(
      (item) =>
        item.note_prefix1 === category.note_prefix1 ||
        item.category_slug === category.category_slug ||
        item.frontend_name1 === category.frontend_name1
    )
    if (exists) return false

    next.push({
      type: category.type || 'docs',
      frontend_name1: category.frontend_name1,
      category_slug: category.category_slug,
      note_prefix1: category.note_prefix1,
      cover: category.cover || '',
      sort_order: category.sort_order || (next.length + 1) * 10,
      enabled: category.enabled !== false,
      children: category.children || [],
      prefix1: category.note_prefix1,
      primaryName: category.frontend_name1,
      primarySlug: category.category_slug,
      dir: category.category_slug
    })
    await saveRegistry(next)
    return true
  }

  async function addSecondaryCategory(
    notePrefix1: string,
    child: Pick<CategoryRegistryChild, 'frontend_name2' | 'note_prefix2'> &
      Partial<CategoryRegistryChild>
  ): Promise<boolean> {
    const next = normalizeRegistry(registry.value)
    const primary = next.find((category) => category.note_prefix1 === notePrefix1)
    if (!primary) return false
    const exists = primary.children.some((item) => item.note_prefix2 === child.note_prefix2)
    if (exists) return false

    primary.children.push({
      frontend_name2: child.frontend_name2,
      note_prefix2: child.note_prefix2,
      sort_order: child.sort_order || (primary.children.length + 1) * 10,
      enabled: child.enabled !== false
    })
    await saveRegistry(next)
    return true
  }

  async function addCustomCategory(parentPrefixOrSlug: string, name: string): Promise<boolean> {
    const primary = getPrimaryByPrefix(parentPrefixOrSlug) || getPrimaryBySlug(parentPrefixOrSlug)
    if (!primary) return false
    const prefix = name
      .trim()
      .toLowerCase()
      .replace(/\s+/g, '_')
      .replace(/[^a-z0-9_]/g, '')
    if (!prefix) return false
    return addSecondaryCategory(primary.note_prefix1, {
      frontend_name2: name.trim(),
      note_prefix2: prefix
    })
  }

  async function removeCustomCategory(name: string): Promise<void> {
    const next = normalizeRegistry(registry.value)
    for (const category of next) {
      category.children = category.children.filter((child) => child.frontend_name2 !== name)
    }
    await saveRegistry(next)
  }

  async function removeSecondaryCategory(notePrefix1: string, notePrefix2: string): Promise<void> {
    const next = normalizeRegistry(registry.value)
    const primary = next.find((category) => category.note_prefix1 === notePrefix1)
    if (!primary) return
    primary.children = primary.children.filter((child) => child.note_prefix2 !== notePrefix2)
    await saveRegistry(next)
  }

  async function updateSecondaryCategoryEnabled(
    notePrefix1: string,
    notePrefix2: string,
    enabled: boolean
  ): Promise<boolean> {
    const next = normalizeRegistry(registry.value)
    const primary = next.find((category) => category.note_prefix1 === notePrefix1)
    const child = primary?.children.find((item) => item.note_prefix2 === notePrefix2)
    if (!child) return false
    child.enabled = enabled
    await saveRegistry(next)
    return true
  }

  async function updatePrimaryCategorySortOrder(
    notePrefix1: string,
    sortOrder: number
  ): Promise<boolean> {
    const next = normalizeRegistry(registry.value)
    const primary = next.find((category) => category.note_prefix1 === notePrefix1)
    if (!primary) return false
    primary.sort_order = sortOrder
    await saveRegistry(next)
    return true
  }

  async function updateSecondaryCategorySortOrder(
    notePrefix1: string,
    notePrefix2: string,
    sortOrder: number
  ): Promise<boolean> {
    const next = normalizeRegistry(registry.value)
    const primary = next.find((category) => category.note_prefix1 === notePrefix1)
    const child = primary?.children.find((item) => item.note_prefix2 === notePrefix2)
    if (!child) return false
    child.sort_order = sortOrder
    await saveRegistry(next)
    return true
  }

  async function resetCustomCategories(): Promise<void> {
    await saveRegistry(FALLBACK_REGISTRY)
  }

  return {
    registry,
    isLoading,
    error,
    loaded,
    allCategories,
    customCategories,
    primaryCategories,
    enabledPrimaryCategories,
    fetchRegistry,
    saveRegistry,
    getPrimaryByPrefix,
    getPrimaryBySlug,
    getSecondaryByPrefix,
    getSubCategories,
    addPrimaryCategory,
    addSecondaryCategory,
    addCustomCategory,
    removeCustomCategory,
    removeSecondaryCategory,
    updateSecondaryCategoryEnabled,
    updatePrimaryCategorySortOrder,
    updateSecondaryCategorySortOrder,
    resetCustomCategories
  }
})
