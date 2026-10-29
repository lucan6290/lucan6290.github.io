export interface ParsedFrontMatter {
  frontMatter: Record<string, unknown>
  body: string
}

const BOM = '\uFEFF'

export function stripLeadingBom(content: string): string {
  if (content.startsWith(BOM)) return content.slice(1)
  return content
}

export function parseFrontMatter(content: string): ParsedFrontMatter {
  const cleaned = stripLeadingBom(content)

  if (!cleaned.startsWith('---')) {
    return { frontMatter: {}, body: cleaned }
  }

  const endIndex = cleaned.indexOf('---', 3)
  if (endIndex === -1) {
    return { frontMatter: {}, body: cleaned }
  }

  const yamlBlock = cleaned.slice(3, endIndex).trim()
  const body = cleaned.slice(endIndex + 3).replace(/^\n+/, '')
  const frontMatter = parseSimpleYaml(yamlBlock)

  return { frontMatter, body }
}

/** 简单 YAML 解析（仅支持 key: value 格式） */
function parseSimpleYaml(yaml: string): Record<string, unknown> {
  const result: Record<string, unknown> = {}
  const lines = yaml.split('\n')

  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) continue

    const colonIndex = trimmed.indexOf(':')
    if (colonIndex === -1) continue

    const key = trimmed.slice(0, colonIndex).trim()
    let value = trimmed.slice(colonIndex + 1).trim()

    // 去引号
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1)
    }

    // 类型推断
    if (value === 'true') result[key] = true
    else if (value === 'false') result[key] = false
    else if (value === 'null' || value === '~') result[key] = null
    else if (/^-?\d+$/.test(value)) result[key] = parseInt(value, 10)
    else if (/^-?\d+\.\d+$/.test(value)) result[key] = parseFloat(value)
    else result[key] = value
  }

  return result
}

export function stringifyFrontMatter(frontMatter: Record<string, unknown>): string {
  const lines = Object.entries(frontMatter).map(([key, value]) => {
    if (value === null || value === undefined) return `${key}: null`
    if (typeof value === 'boolean') return `${key}: ${value}`
    if (typeof value === 'number') return `${key}: ${value}`
    if (Array.isArray(value)) {
      const items = value.map((item) => `  - ${item}`).join('\n')
      return `${key}:\n${items}`
    }
    return `${key}: ${value}`
  })
  return `---\n${lines.join('\n')}\n---\n`
}
