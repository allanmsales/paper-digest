import { useCallback, useEffect, useState } from 'react'

import { fetchSession, recordView } from './api'
import type { FeedSession } from './types'

const POLL_MS = 10_000

/** Loads a session of posts (polling while the feed is being built) and
 *  tracks which posts the reader finished. */
export function useFeedSession(paperId: string, onLoad?: () => void) {
  const [session, setSession] = useState<FeedSession | null>(null)
  const [done, setDone] = useState<Set<number>>(new Set())
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      setSession(await fetchSession(paperId))
      setDone(new Set())
      setError(null)
      onLoad?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load the feed.')
    }
  }, [paperId, onLoad])

  useEffect(() => {
    load()
  }, [load])

  // The first build takes a few minutes: poll until it's ready.
  useEffect(() => {
    if (session?.status !== 'building') return
    const timer = window.setTimeout(load, POLL_MS)
    return () => window.clearTimeout(timer)
  }, [session, load])

  function markDone(postId: number, correct: boolean | null) {
    if (done.has(postId)) return
    recordView(postId, correct)
    setDone((current) => new Set(current).add(postId))
  }

  const posts = session?.posts ?? []
  const allDone = posts.length > 0 && posts.every((post) => done.has(post.id))
  const progress = session?.total_concepts
    ? Math.round((session.seen_concepts / session.total_concepts) * 100)
    : 0

  return { session, posts, done, error, load, markDone, allDone, progress }
}
