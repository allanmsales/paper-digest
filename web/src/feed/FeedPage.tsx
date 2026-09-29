import { useCallback, useEffect, useState } from 'react'

import { fetchSession, recordView } from './api'
import { PostCard } from './PostCard'
import type { FeedSession } from './types'
import './feed.css'

const POLL_MS = 10_000

type Props = {
  paperId: string
}

/** A short, finite feed of posts about the paper's prerequisites. */
export function FeedPage({ paperId }: Props) {
  const [session, setSession] = useState<FeedSession | null>(null)
  const [done, setDone] = useState<Set<number>>(new Set())
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      setSession(await fetchSession(paperId))
      setDone(new Set())
      setError(null)
      window.scrollTo({ top: 0 })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load the feed.')
    }
  }, [paperId])

  useEffect(() => {
    load()
  }, [load])

  // The first build takes a few minutes: poll until it's ready.
  useEffect(() => {
    if (session?.status !== 'building') return
    const timer = window.setTimeout(load, POLL_MS)
    return () => window.clearTimeout(timer)
  }, [session, load])

  function handleDone(postId: number, correct: boolean | null) {
    recordView(postId, correct)
    setDone((current) => new Set(current).add(postId))
  }

  const posts = session?.posts ?? []
  const allDone = posts.length > 0 && posts.every((post) => done.has(post.id))
  const progress = session?.total_concepts
    ? Math.round((session.seen_concepts / session.total_concepts) * 100)
    : 0

  return (
    <div className="feed">
      <header className="feed__header">
        <h1>Learning feed</h1>
        {session?.status === 'ready' && (
          <div className="feed__progress" title={`${progress}% of concepts`}>
            <div className="feed__bar">
              <div style={{ width: `${progress}%` }} />
            </div>
            <span>
              {session.seen_concepts} of {session.total_concepts} concepts
            </span>
          </div>
        )}
      </header>

      <main className="feed__main">
        {error && <p className="feed__note feed__note--error">{error}</p>}

        {!session && !error && <p className="feed__note">Loading…</p>}

        {session?.status === 'building' && (
          <p className="feed__note">
            Preparing your feed from the paper’s prerequisites. The first time takes a few
            minutes. This page updates by itself.
          </p>
        )}

        {session?.status === 'error' && (
          <p className="feed__note feed__note--error">
            The feed could not be prepared: {session.error}
          </p>
        )}

        {posts.map((post) => (
          <PostCard
            key={post.id}
            post={post}
            onDone={(correct) => handleDone(post.id, correct)}
          />
        ))}

        {session?.status === 'ready' && (
          <section className={`feed__end${allDone ? ' is-complete' : ''}`}>
            {posts.length === 0 ? (
              <p>You’ve gone through every post for this paper. 🎉</p>
            ) : allDone ? (
              <p>Done for today. 🎉 Take a break, or keep going slowly.</p>
            ) : (
              <p>
                {done.size} of {posts.length} done in this session.
              </p>
            )}
            {session.remaining_posts > 0 && (
              <button onClick={load} disabled={!allDone}>
                8 more
              </button>
            )}
          </section>
        )}
      </main>
    </div>
  )
}
