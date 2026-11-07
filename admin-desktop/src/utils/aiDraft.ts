export type AiOperation = 'generate' | 'rewrite'
type DocumentKey = string | number

export class AiDraftError extends Error {}

interface DraftRequest {
  operation: AiOperation
  buffer: string
  documentKey: DocumentKey
  prefix: string
  newline: string
  before: string
}

function splitBuffer(buffer: string) {
  const bom = buffer.startsWith('\uFEFF') ? '\uFEFF' : ''
  const text = buffer.slice(bom.length)
  const delimiter = /^\s*---\s*$/
  const lines = text.matchAll(/[^\r\n]*(?:\r\n|\n|\r|$)/g)
  if (!delimiter.test(lines.next().value?.[0] ?? '')) return { prefix: bom, body: text }
  for (const line of lines) {
    if (!delimiter.test(line[0])) continue
    const offset = line.index + line[0].length
    return { prefix: bom + text.slice(0, offset), body: text.slice(offset) }
  }
  throw new AiDraftError('YAML 头部缺少结束分隔符，请检查正文。')
}

function bodyWithoutHeader(markdown: string) {
  const withoutLeadingLines = (text: string) => text.replace(/^(?:[ \t]*(?:\r\n|\n|\r))+/, '')
  const clean = withoutLeadingLines(markdown.replace(/^\uFEFF/, ''))
  const fenced = /^(\x60{3,}|~{3,})(?:markdown|md)[ \t]*\r?\n([\s\S]*?)\r?\n\1[ \t]*(?:\r?\n)*$/i.exec(clean)
  const text = withoutLeadingLines(splitBuffer(fenced ? fenced[2] : clean).body)
  if (!text.trim() || splitBuffer(text).prefix) throw new AiDraftError('AI 没有返回可采用的正文，请调整要求后重试。')
  return text
}

export class AiDraftSession {
  private request: DraftRequest | null = null
  suggestion: { before: string; after: string } | null = null

  get pending() {
    return this.request !== null && this.suggestion === null
  }

  invalidate() {
    this.request = null
    this.suggestion = null
  }

  begin(operation: AiOperation, buffer: string, documentKey: DocumentKey) {
    const { prefix, body } = splitBuffer(buffer)
    const newline = buffer.match(/\r\n|\n|\r/)?.[0] ?? '\n'
    const request = { operation, buffer, documentKey, prefix, newline, before: body }
    this.request = request
    this.suggestion = null
    return request
  }

  isCurrent(request: DraftRequest) {
    return this.request === request
  }

  complete(request: DraftRequest, markdown: string) {
    if (!this.isCurrent(request)) return false
    const body = bodyWithoutHeader(markdown)
    const leadingLines = request.before.match(/^(?:[ \t]*(?:\r\n|\n|\r))+/)?.[0] ?? ''
    const after = leadingLines + body.replace(/\r\n|\r|\n/g, request.newline)
    this.suggestion = { before: request.before, after }
    return true
  }

  accept(buffer: string, documentKey: DocumentKey) {
    const request = this.request
    if (!request || !this.suggestion || request.buffer !== buffer || request.documentKey !== documentKey) return null
    const separator = request.prefix && request.prefix !== '\uFEFF' && !/[\r\n]$/.test(request.prefix) ? request.newline : ''
    const next = request.prefix + separator + this.suggestion.after
    this.invalidate()
    return next
  }
}