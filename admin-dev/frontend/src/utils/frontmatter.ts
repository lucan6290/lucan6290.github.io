/**
 * Front Matter 解析与序列化工具
 * 浏览器兼容，不依赖 Node.js 模块
 */

/**
 * 轻量 Front Matter 解析器（替代 gray-matter）
 * 仅支持博客用到的简单 YAML 格式
 */
function parseMatter(content: string): { data: Record<string, unknown>; content: string } {
  const trimmed = content.replace(/^﻿/, '')
  const match = trimmed.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/)
  if (!match) {
    return { data: {}, content: trimmed }
  }
  const yaml = match[1]
  const body = trimmed.slice(match[0].length)
  return { data: parseSimpleYaml(yaml), content: body }
}

/**
 * 简易 YAML 解析器
 * 支持 key: value、列表、嵌套数组 [[a, b]] 格式
 */
function parseSimpleYaml(yaml: string): Record<string, unknown> {
  const result: Record<string, unknown> = {}
  const lines = yaml.split(/\r?\n/)
  let currentKey = ''
  let currentList: unknown[] = []

  function flushList() {
    if (currentKey && currentList.length > 0) {
      result[currentKey] = currentList
      currentKey = ''
      currentList = []
    }
  }

  for (const rawLine of lines) {
    // 跳过空行
    if (rawLine.trim() === '') continue

    // 列表项：  - value 或  - [a, b]
    const listMatch = rawLine.match(/^(\s+)-\s+(.*)$/)
    if (listMatch) {
      let val: unknown = listMatch[2].trim()
      // 嵌套数组格式：[a, b]
      const arrMatch = (val as string).match(/^\[(.*)\]$/)
      if (arrMatch) {
        val = arrMatch[1].split(',').map(s => s.trim())
      }
      // 自动转换布尔值和数字
      else if (val === 'true') val = true
      else if (val === 'false') val = false
      else if (/^\d+$/.test(val as string)) val = Number(val)
      // 去除引号
      else {
        val = unwrapQuotes(val as string)
      }
      currentList.push(val)
      continue
    }

    // 新的 key: value 行，先 flush 之前的列表
    flushList()

    const kvMatch = rawLine.match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)$/)
    if (kvMatch) {
      const key = kvMatch[1]
      let val = kvMatch[2].trim()
      if (val === '') {
        // 空 value → 后面跟列表
        currentKey = key
        currentList = []
        continue
      }
      // 自动转换类型
      if (val === 'true') result[key] = true
      else if (val === 'false') result[key] = false
      else if (/^\d+$/.test(val)) result[key] = Number(val)
      else {
        // 内联数组格式：[a, b, c]
        const inlineArrMatch = val.match(/^\[(.*)\]$/)
        if (inlineArrMatch) {
          result[key] = inlineArrMatch[1].split(',').map(s => unwrapQuotes(s.trim()))
        } else {
          result[key] = unwrapQuotes(val)
        }
      }
    }
  }

  flushList()
  return result
}

/**
 * 去除 YAML 字符串两端的引号
 */
function unwrapQuotes(val: string): string {
  if (
    (val.startsWith('"') && val.endsWith('"')) ||
    (val.startsWith("'") && val.endsWith("'"))
  ) {
    return val.slice(1, -1)
  }
  return val
}
import type { FrontMatter } from '@/types/api'

/**
 * 解析 Markdown 文件的 Front Matter
 * @param content Markdown 文件完整内容
 * @returns 解析后的 Front Matter 和正文内容
 */
export function parseFrontMatter(content: string): {
  frontMatter: FrontMatter
  body: string
} {
  try {
    const { data, content: body } = parseMatter(content)
    return {
      frontMatter: data as unknown as FrontMatter,
      body
    }
  } catch (error) {
    console.error('解析 Front Matter 失败:', error)
    throw new Error('文章格式错误：无法解析 Front Matter')
  }
}

/**
 * 序列化 Front Matter 为 YAML 格式
 * @param frontMatter Front Matter 对象
 * @returns YAML 格式的字符串（不包含 --- 分隔符）
 */
export function serializeFrontMatter(frontMatter: Partial<FrontMatter>): string {
  const lines: string[] = []

  // 标题（必须）
  lines.push(`title: ${escapeYamlString(frontMatter.title || '未命名文章')}`)

  // 日期（必须）
  const dateStr = frontMatter.date || new Date().toISOString().replace('T', ' ').slice(0, 19)
  lines.push(`date: ${dateStr}`)

  // 更新日期（可选）
  if (frontMatter.updated) {
    lines.push(`updated: ${frontMatter.updated}`)
  }

  lines.push('')

  // 分类（必须）— 嵌套数组格式 [[一级, 二级]]
  lines.push('categories:')
  if (Array.isArray(frontMatter.categories) && frontMatter.categories.length > 0) {
    // 如果已有嵌套数组格式（categories[0] 是数组），直接使用
    if (Array.isArray(frontMatter.categories[0])) {
      for (const cat of frontMatter.categories) {
        const catArr = cat as unknown as string[]
        lines.push(`  - [${catArr.map(c => escapeYamlString(c)).join(', ')}]`)
      }
    } else {
      // 扁平列表格式，转换为嵌套数组 [[一级, 二级]]
      const cats = frontMatter.categories as string[]
      lines.push(`  - [${cats.map(c => escapeYamlString(c)).join(', ')}]`)
    }
  } else {
    lines.push('  - [未分类]')
  }

  lines.push('')

  // 标签（可选）
  lines.push('tags:')
  if (Array.isArray(frontMatter.tags) && frontMatter.tags.length > 0) {
    frontMatter.tags.forEach((tag) => {
      lines.push(`  - ${escapeYamlString(tag)}`)
    })
  }

  // 描述（可选）
  if (frontMatter.description) {
    lines.push('')
    lines.push(`description: ${escapeYamlString(frontMatter.description)}`)
  }

  // 布局（可选）
  if (frontMatter.layout) {
    lines.push('')
    lines.push(`layout: ${frontMatter.layout}`)
  }

  // 评论（可选）
  if (frontMatter.comments !== undefined) {
    lines.push('')
    lines.push(`comments: ${frontMatter.comments}`)
  }

  // 永久链接（可选）
  if (frontMatter.permalink) {
    lines.push('')
    lines.push(`permalink: ${frontMatter.permalink}`)
  }

  // 摘录（可选）
  if (frontMatter.excerpt) {
    lines.push('')
    lines.push(`excerpt: ${escapeYamlString(frontMatter.excerpt)}`)
  }

  // 发布状态（可选）
  if (frontMatter.published !== undefined) {
    lines.push('')
    lines.push(`published: ${frontMatter.published}`)
  }

  // 语言（可选）
  if (frontMatter.lang) {
    lines.push('')
    lines.push(`lang: ${frontMatter.lang}`)
  }

  // 封面图（可选）
  if (frontMatter.cover) {
    lines.push('')
    lines.push(`cover: ${frontMatter.cover}`)
  }

  // 置顶（可选）
  if (frontMatter.sticky !== undefined) {
    lines.push('')
    lines.push(`sticky: ${frontMatter.sticky}`)
  }

  // Slug（可选）
  if (frontMatter.slug) {
    lines.push('')
    lines.push(`slug: ${frontMatter.slug}`)
  }

  // 状态（可选）
  if (frontMatter.status) {
    lines.push('')
    lines.push(`status: ${frontMatter.status}`)
  }

  // 系列（可选）
  if (frontMatter.series) {
    lines.push('')
    lines.push(`series: ${escapeYamlString(frontMatter.series)}`)

    if (frontMatter.series_order !== undefined) {
      lines.push(`series_order: ${frontMatter.series_order}`)
    }
  }

  return lines.join('\n')
}

/**
 * 提取 Markdown 内容（不含 Front Matter）
 * @param content Markdown 文件完整内容
 * @returns 正文内容
 */
export function extractContent(content: string): string {
  const { content: body } = parseMatter(content)
  return body
}

/**
 * 组合 Front Matter 和 Markdown 内容
 * @param frontMatter Front Matter 对象
 * @param body 正文内容
 * @returns 完整的 Markdown 文件内容
 */
export function buildMarkdown(frontMatter: Partial<FrontMatter>, body: string = ''): string {
  const yamlStr = serializeFrontMatter(frontMatter)
  return `---\n${yamlStr}\n---\n${body}`
}

/**
 * 转义 YAML 字符串
 * 处理包含特殊字符的字符串
 */
function escapeYamlString(str: string): string {
  if (!str) return str

  // 如果字符串包含特殊字符，用引号包裹
  const specialChars = /[:#\n\r\t{}[\],&*?|<>=!%@`]/
  if (specialChars.test(str) || str.startsWith(' ') || str.endsWith(' ')) {
    // 转义双引号
    const escaped = str.replace(/"/g, '\\"')
    return `"${escaped}"`
  }

  return str
}

/**
 * 验证 Front Matter 是否有效
 * @param frontMatter Front Matter 对象
 * @returns 验证结果
 */
export function validateFrontMatter(frontMatter: Partial<FrontMatter>): {
  valid: boolean
  errors: string[]
} {
  const errors: string[] = []

  // 标题是必须的
  if (!frontMatter.title || frontMatter.title.trim() === '') {
    errors.push('标题不能为空')
  }

  // 日期格式验证
  if (frontMatter.date) {
    const dateRegex = /^\d{4}-\d{2}-\d{2}(\s+\d{2}:\d{2}:\d{2})?$/
    if (!dateRegex.test(frontMatter.date)) {
      errors.push('日期格式无效，应为 YYYY-MM-DD 或 YYYY-MM-DD HH:mm:ss')
    }
  }

  // 更新日期格式验证
  if (frontMatter.updated) {
    const dateRegex = /^\d{4}-\d{2}-\d{2}(\s+\d{2}:\d{2}:\d{2})?$/
    if (!dateRegex.test(frontMatter.updated)) {
      errors.push('更新日期格式无效，应为 YYYY-MM-DD 或 YYYY-MM-DD HH:mm:ss')
    }
  }

  // 状态验证
  if (frontMatter.status && !['draft', 'wip', 'published'].includes(frontMatter.status)) {
    errors.push('状态值无效，应为 draft、wip 或 published')
  }

  return {
    valid: errors.length === 0,
    errors
  }
}

/**
 * 更新 Front Matter
 * 保留原有内容，只更新指定字段
 * @param content 原始 Markdown 内容
 * @param updates 要更新的字段
 * @returns 更新后的 Markdown 内容
 */
export function updateFrontMatter(
  content: string,
  updates: Partial<FrontMatter>
): string {
  const { frontMatter, body } = parseFrontMatter(content)
  const updated = { ...frontMatter, ...updates }

  // 如果有更新，自动设置 updated 时间
  if (Object.keys(updates).length > 0 && !updates.updated) {
    updated.updated = new Date().toISOString().replace('T', ' ').slice(0, 19)
  }

  return buildMarkdown(updated, body)
}

/**
 * 获取默认 Front Matter
 * @param title 文章标题
 * @param categories 分类
 * @returns 默认 Front Matter 对象
 */
export function getDefaultFrontMatter(
  title: string = '未命名文章',
  categories: string[] = ['未分类']
): FrontMatter {
  const now = new Date()
  const dateStr = now.toISOString().replace('T', ' ').slice(0, 19)

  return {
    title,
    date: dateStr,
    categories,
    tags: [],
    description: '',
    status: 'draft',
    lang: 'zh-CN',
    comments: true,
    published: true
  }
}