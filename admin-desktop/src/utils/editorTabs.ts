import { reactive, shallowRef } from 'vue'
import { createArticleTemplate } from './articleTemplate'
import { DocumentSession } from './documentSession'

export function newDraftId() {
  return crypto.randomUUID()
}

function makeTab(path: string | null, draft: string | undefined, directory: string) {
  const startedAt = new Date()
  const session = reactive(new DocumentSession())
  session.begin(path, path ? '' : createArticleTemplate(startedAt))
  return reactive({
    id: draft || newDraftId(), session, startedAt, directory, filename: '',
    purpose: path ? 'auto' : 'article', draftNotice: '',
  })
}

export type EditorTab = ReturnType<typeof makeTab>
export const editorTabs = shallowRef<EditorTab[]>([])
let lastTab: EditorTab | null = null

export function activateEditorTab(path: string | null, draft?: string, directory = '') {
  let active = path ? editorTabs.value.find(tab => tab.session.path === path)
    : draft ? editorTabs.value.find(tab => tab.id === draft)
      : lastTab
  if (!active) {
    active = makeTab(path, draft, directory)
    editorTabs.value = [...editorTabs.value, active]
  }
  lastTab = active
  return active
}

export function removeEditorTab(tab: EditorTab) {
  editorTabs.value = editorTabs.value.filter(item => item.id !== tab.id)
  if (lastTab?.id === tab.id) lastTab = editorTabs.value.slice(-1)[0] ?? null
}

export function clearEditorTabs() {
  editorTabs.value = []
  lastTab = null
}

export function editorTabQuery(tab: EditorTab) {
  return tab.session.path ? { id: tab.session.path } : { draft: tab.id, directory: tab.directory }
}

export function editorTabLabel(tab: EditorTab) {
  return tab.session.path?.split('/').slice(-1)[0] || tab.filename || '新建文档'
}

export interface PathMove { before: string; after: string }

export function relocatePath(path: string, moves: PathMove[]) {
  const moved = moves.find(item => path === item.before || path.startsWith(item.before + '/'))
  return moved ? moved.after + path.slice(moved.before.length) : path
}

export function relocateEditorTabs(moves: PathMove[]) {
  for (const tab of editorTabs.value) {
    const original = tab.session.path
    if (!original || tab.session.dirty || tab.session.saving) continue
    const moved = relocatePath(original, moves)
    if (moved !== original) {
      tab.session.begin(moved)
      tab.purpose = 'auto'
    }
  }
}
