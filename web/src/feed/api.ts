import type { FeedSession } from './types'

export function startFeedBuild(paperId: string): void {
  fetch(`/api/feed/${paperId}/build`, { method: 'POST' }).catch(() => {
    // Best effort: the feed page starts the build too.
  })
}

export async function fetchSession(paperId: string): Promise<FeedSession> {
  const response = await fetch(`/api/feed/${paperId}/session`)
  if (!response.ok) throw new Error(`Request failed (${response.status}).`)
  return response.json()
}

export function recordView(postId: number, correct: boolean | null): void {
  fetch('/api/feed/view', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ post_id: postId, correct }),
  }).catch(() => {
    // Not recorded: the post simply shows up again next session.
  })
}
