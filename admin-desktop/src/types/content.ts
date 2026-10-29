export interface DocumentSummary {
  relative_path: string
  name: string
  title: string
  section: string
  kind: 'article' | 'introduction'
  tags: string[]
  description: string
  date: string | null
  updated: string | null
  modified_at: string
  version: string
}

export interface ContentDetail extends DocumentSummary {
  raw_content: string
  frontmatter: Record<string, unknown>
}

export interface ContentDirectory {
  relative_path: string
  name: string
  label: string
  section: string
}

export interface ContentIndex {
  directories: ContentDirectory[]
  documents: DocumentSummary[]
}

export interface ContentVersion {
  exists: boolean
  version: string | null
}

export interface ContentHealth {
  service: 'xiaocancoding-content'
  api_version: 1
  project_root: string
  content_root: string
}
