export type FeedPost = {
  id: number
  concept: string
  kind: 'lesson' | 'flip' | 'quiz'
  title: string
  body: string
  back: string | null
  options: string[]
  answer_index: number | null
  why_it_matters: string
}

export type FeedSession = {
  status: 'building' | 'ready' | 'error'
  error: string | null
  posts: FeedPost[]
  seen_concepts: number
  total_concepts: number
  remaining_posts: number
}
