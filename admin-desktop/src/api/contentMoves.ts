import { request } from './content'

export type MoveKind = 'document' | 'directory'

interface PathChange {
  before: string
  after: string
}

export interface MovePlan {
  source: string
  destination: string
  kind: MoveKind
  moves: PathChange[]
  files: (PathChange & { rewritten: boolean })[]
  routes: PathChange[]
  plan_id: string
}

export interface ContentGraph {
  documents: string[]
  edges: { source: string; target: string }[]
}

export const contentMoves = {
  plan: (source: string, destination: string, kind: MoveKind) =>
    request<MovePlan>('/api/v1/moves/plan', 'POST', { source, destination, kind }, 60000),
  apply: (plan: MovePlan) => request<MovePlan>('/api/v1/moves', 'POST', {
    source: plan.source, destination: plan.destination, kind: plan.kind, plan_id: plan.plan_id,
  }, 60000),
  links: () => request<ContentGraph>('/api/v1/links'),
}
