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
  /** Finished by this user earlier. */
  done: boolean
}

/** The user's whole feed for a paper: one fixed set of posts. */
export type FeedSession = {
  status: 'building' | 'ready' | 'error'
  error: string | null
  posts: FeedPost[]
  done: number
}
