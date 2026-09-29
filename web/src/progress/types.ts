export type MediaKind = 'podcast' | 'video' | 'reading'
export type MilestoneItem = 'reading' | 'summary'

/** Each Learning Path step from 0 to 1; completion is their average. */
export type Progress = {
  reading: number
  summary: number
  podcast: number
  video: number
  feed: number
  check: number
  completion: number
  confirmed: MilestoneItem[]
}

export type NodeState = 'not_started' | 'learning' | 'solid' | 'needs_work'

export type MapNode = {
  name: string
  requires: string[]
  state: NodeState
  posts: number
  seen: number
  is_main: boolean
}

export type KnowledgeMapData = {
  status: 'none' | 'building' | 'ready'
  nodes: MapNode[]
}

export type Place = 'reading' | 'summary' | 'podcast' | 'video' | 'feed' | 'check' | 'map'

export type Assessment = {
  score: number
  verdict: string
  strengths: string[]
  improvements: { concept: string | null; why: string; place: Place }[]
  created_at: string
}
