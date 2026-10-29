import type { ContentDetail, ContentVersion } from '../types/content'
import { mergeSavedUpdated } from './articleTemplate'

interface ReadApi {
  version(path: string): Promise<ContentVersion>
  read(path: string): Promise<ContentDetail>
}

interface WriteApi {
  create(path: string, raw: string, article?: boolean): Promise<ContentDetail>
  save(path: string, raw: string, version: string, article?: boolean): Promise<ContentDetail>
}

function displayText(raw: string) {
  return raw.replace(/^\uFEFF/, '').replace(/\r\n/g, '\n')
}

export class DocumentSession {
  generation = 0
  path: string | null = null
  baseline: ContentDetail | null = null
  text = ''
  external: ContentDetail | null = null
  missing = false
  saving = false
  externalUpdated = false
  private checking: Promise<void> | null = null
  private writeRevision = 0
  private draftBaseline = ''

  get dirty() {
    return this.text !== (this.baseline ? displayText(this.baseline.raw_content) : this.draftBaseline)
  }

  begin(path: string | null, draft = '') {
    this.generation++
    this.path = path
    this.baseline = null
    this.text = displayText(draft)
    this.draftBaseline = this.text
    this.external = null
    this.missing = false
    this.saving = false
    this.externalUpdated = false
    this.checking = null
  }

  replaceDraft(text: string) {
    if (this.path || this.baseline || this.dirty) return false
    this.text = displayText(text)
    this.draftBaseline = this.text
    return true
  }

  load(detail: ContentDetail, generation: number) {
    if (generation !== this.generation) return
    this.path = detail.relative_path
    this.baseline = detail
    this.text = displayText(detail.raw_content)
    this.external = null
    this.missing = false
  }

  rawContent() {
    if (!this.baseline) return displayText(this.text)
    if (this.baseline && !this.dirty) return this.baseline.raw_content
    const raw = this.baseline?.raw_content || ''
    const newline = raw.includes('\r\n') ? '\r\n' : '\n'
    return (raw.startsWith('\uFEFF') ? '\uFEFF' : '') + this.text.replace(/\r\n/g, '\n').replace(/\n/g, newline)
  }

  check(api: ReadApi): Promise<void> {
    if (!this.path || !this.baseline || this.saving) return Promise.resolve()
    if (this.checking) return this.checking
    const generation = this.generation
    const revision = this.writeRevision
    const path = this.path
    const current = () => generation === this.generation && revision === this.writeRevision
    const checking = (async () => {
      const disk = await api.version(path)
      if (!current()) return
      if (!disk.exists) {
        this.missing = true
        this.external = null
        return
      }
      if (disk.version === this.baseline?.version) {
        this.missing = false
        this.external = null
        return
      }
      const detail = await api.read(path)
      if (!current()) return
      if (this.dirty) {
        this.external = detail
        this.missing = false
      } else {
        this.load(detail, generation)
        this.externalUpdated = true
      }
    })()
    this.checking = checking
    void checking.finally(() => {
      if (this.checking === checking) this.checking = null
    }).catch(() => {})
    return checking
  }

  async save(api: WriteApi, newPath?: string, article?: boolean) {
    if (this.saving) throw new Error('保存正在进行，请稍后重试')
    if (this.baseline && !this.dirty) return this.baseline
    if (this.path && !this.baseline) throw new Error('文档尚未成功读取，不能保存')
    const path = this.path || newPath
    if (!path) throw new Error('请输入实际文件名')
    const generation = this.generation
    const text = this.text
    const raw = this.rawContent()
    this.saving = true
    this.writeRevision++
    try {
      const detail = this.baseline
        ? await api.save(path, raw, this.baseline.version, article)
        : await api.create(path, raw, article ?? true)
      if (generation === this.generation) {
        this.path = detail.relative_path
        this.baseline = detail
        if (this.text === text) this.text = displayText(detail.raw_content)
        else this.text = mergeSavedUpdated(this.text, text, displayText(detail.raw_content))
        this.external = null
        this.missing = false
        this.externalUpdated = false
      }
      return detail
    } finally {
      if (generation === this.generation) this.saving = false
    }
  }

  async saveAs(api: Pick<WriteApi, 'create'>, path: string, article = false) {
    if (this.saving) throw new Error('保存正在进行，请稍后重试')
    const generation = this.generation
    const text = this.text
    this.saving = true
    this.writeRevision++
    try {
      const detail = await api.create(path, displayText(text), article)
      if (generation === this.generation) {
        this.path = detail.relative_path
        this.baseline = detail
        if (this.text === text) this.text = displayText(detail.raw_content)
        else this.text = mergeSavedUpdated(this.text, text, displayText(detail.raw_content))
        this.external = null
        this.missing = false
        this.externalUpdated = false
      }
      return detail
    } finally {
      if (generation === this.generation) this.saving = false
    }
  }
}
