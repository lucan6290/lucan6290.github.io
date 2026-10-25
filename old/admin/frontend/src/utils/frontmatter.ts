/**
 * Front Matter 解析与序列化工具
 * 浏览器兼容，不依赖 Node.js 模块
 */

/**
 * 轻量 Front Matter 解析器（替代 gray-matter）
 * 仅支持博客用到的简单 YAML 格式
 */
function parseMatter(content: string): { data: Record<string, unknown>; content: string } {
  const trimmed = stripLeadingBom(content)
  const match = trimmed.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/)
  if (!match) {
    return { data: {}, content: trimmed }
  }
  const yaml = match[1]
  const body = trimmed.slice(match[0].length)
  return { data: parseSimpleYaml(yaml), content: body }
}

export function stripLeadingBom(content: string): string {
  return content.replace(/^\ufeff/, '')
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
  let currentNestedObj: Record<string, unknown> | null = null

  // 收尾：currentKey 下可能是列表（tags/categories）或嵌套对象（last_update）
  function flushPending() {
    if (!currentKey) {
      currentList = []
      currentNestedObj = null
      return
    }
    if (currentList.length > 0) {
      result[currentKey] = currentList
    } else if (currentNestedObj && Object.keys(currentNestedObj).length > 0) {
      result[currentKey] = currentNestedObj
    }
    currentKey = ''
    currentList = []
    currentNestedObj = null
  }

  for (const rawLine of lines) {
    // 跳过空行
    if (rawLine.trim() === '') continue

    // 列表项：  - value 或  - [a, b]
    const listMatch = rawLine.match(/^(\s+)-\s+(.*)$/)
    if (listMatch) {
      currentList.push(parseScalarOrArray(listMatch[2].trim()))
      continue
    }

    // 嵌套对象子属性：缩进的 key: value（如 last_update 下的 date/author）
    const nestedMatch = rawLine.match(/^(\s{2,})([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.+)$/)
    if (nestedMatch && currentKey) {
      if (currentNestedObj === null) currentNestedObj = {}
      currentNestedObj[nestedMatch[2]] = parseScalarOrArray(nestedMatch[3].trim())
      continue
    }

    // 新的顶层 key: value 行，先 flush 之前的列表/嵌套对象
    flushPending()

    const kvMatch = rawLine.match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)$/)
    if (kvMatch) {
      const key = kvMatch[1]
      const val = kvMatch[2].trim()
      if (val === '') {
        // 空 value → 后面跟列表或嵌套对象，待首个子行决定
        currentKey = key
        currentList = []
        currentNestedObj = null
        continue
      }
      result[key] = parseScalarOrArray(val)
    }
  }

  flushPending()
  return result
}

/**
 * 解析标量或内联数组：复用于顶层值、列表项、嵌套子属性
 * 支持 [a, b] 内联数组、布尔、数字（去引号字符串）
 */
function parseScalarOrArray(raw: string): unknown {
  // 嵌套数组格式：[a, b]
  const arrMatch = raw.match(/^\[(.*)\]$/)
  if (arrMatch) {
    return arrMatch[1].split(',').map(s => unwrapQuotes(s.trim()))
  }
  // 自动转换布尔值和数字
  if (raw === 'true') return true
  if (raw === 'false') return false
  if (/^\d+$/.test(raw)) return Number(raw)
  // 去除引号
  return unwrapQuotes(raw)
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
 * 通用实现：只输出传入对象实际拥有的字段，不注入任何默认值（避免 Hexo 风格污染）
 * @param frontMatter Front Matter 对象
 * @returns YAML 格式的字符串（不包含 --- 分隔符）
 */
export function serializeFrontMatter(frontMatter: Partial<FrontMatter>): string {
  const lines: string[] = []

  for (const [key, value] of Object.entries(frontMatter)) {
    if (value === undefined || value === null) continue

    if (Array.isArray(value)) {
      lines.push(`${key}:`)
      value.forEach((item) => {
        if (Array.isArray(item)) {
          // 嵌套数组 [[a, b]] →  - [a, b]
          lines.push(`  - [${item.map(c => escapeYamlString(String(c))).join(', ')}]`)
        } else {
          lines.push(`  - ${escapeYamlString(String(item))}`)
        }
      })
    } else if (typeof value === 'object' && value !== null) {
      // 嵌套对象（如 last_update）→ 块样式多行 YAML
      lines.push(`${key}:`)
      for (const [subKey, subVal] of Object.entries(value)) {
        if (subVal === undefined || subVal === null) continue
        lines.push(`  ${subKey}: ${escapeYamlString(String(subVal))}`)
      }
    } else if (typeof value === 'string') {
      lines.push(`${key}: ${escapeYamlString(value)}`)
    } else {
      // 数字、布尔直接输出
      lines.push(`${key}: ${value}`)
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
    const dateRegex = /^\d{4}-\d{2}-\d{2}([T\s]+\d{2}:\d{2}:\d{2})?([+-]\d{2}:\d{2}|Z)?$/
    if (!dateRegex.test(frontMatter.date)) {
      errors.push('日期格式无效，应为 YYYY-MM-DD 或 YYYY-MM-DD HH:mm:ss')
    }
  }

  // 更新日期格式验证（Docusaurus 原生 last_update.date）
  const lastUpdateDate = frontMatter.last_update?.date
  if (lastUpdateDate) {
    const dateRegex = /^\d{4}-\d{2}-\d{2}([T\s]+\d{2}:\d{2}:\d{2})?([+-]\d{2}:\d{2}|Z)?$/
    if (!dateRegex.test(lastUpdateDate)) {
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

  // 如果有更新，自动刷新 last_update.date（Docusaurus 原生字段）；author 保留既有值，缺省 lucan
  if (Object.keys(updates).length > 0 && !updates.last_update) {
    updated.last_update = {
      date: new Date().toISOString().replace('T', ' ').slice(0, 19),
      author: frontMatter.last_update?.author || 'lucan'
    }
  }

  return buildMarkdown(updated, body)
}
