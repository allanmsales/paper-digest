import { useCallback, useEffect, useState } from 'react'

import { fetchSession, recordView } from './api'
import { notifyProgress } from '../progress/events'
import type { FeedSession } from './types'

const POLL_MS = 10_000

/** Loads the user's feed (polling while it is being built) and tracks
 *  which posts they finished, including earlier visits. */
export function useFeedSession(paperId: string, onLoad?: () => void) {
  const [session, setSession] = useState<FeedSession | null>(null)
  const [done, setDone] = useState<Set<number>>(new Set())
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const result = await fetchSession(paperId)
      setSession(result)
      setDone(new Set(result.posts.filter((post) => post.done).map((post) => post.id)))
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
    recordView(postId, correct).then(notifyProgress)
    setDone((current) => new Set(current).add(postId))
  }

  const posts = session?.posts ?? []
  const allDone = posts.length > 0 && posts.every((post) => done.has(post.id))
  const progress = posts.length ? Math.round((done.size / posts.length) * 100) : 0

  return { session, posts, done, error, markDone, allDone, progress }
}
