import { useState } from 'react'

import { PostCard } from './PostCard'
import { useFeedSession } from './useFeedSession'
import './feed.css'

type Props = {
  paperId: string
}

/** The learning feed inside the reader's side column, one post at a time. */
export function FeedPanel({ paperId }: Props) {
  const [index, setIndex] = useState<number | null>(null)
  const { session, posts, done, error, markDone, allDone, progress } = useFeedSession(paperId)
  // Resume at the first post not finished yet.
  const firstOpen = posts.findIndex((post) => !post.done)
  const current = index ?? (firstOpen === -1 ? posts.length : firstOpen)

  const post = posts[current]
  const atEnd = current >= posts.length

  return (
    <div className="feed-panel">
      {error && <p className="feed__note feed__note--error">{error}</p>}
      {!session && !error && <p className="analogy__status">Loading…</p>}

      {session?.status === 'building' && (
        <p className="analogy__status">
          Preparing posts from the paper’s prerequisites. The first time takes a few minutes.
        </p>
      )}

      {session?.status === 'error' && (
        <p className="feed__note feed__note--error">
          The feed could not be prepared: {session.error}
        </p>
      )}

      {session?.status === 'ready' && (
        <>
          <div className="feed__progress" title={`${progress}% done`}>
            <div className="feed__bar">
              <div style={{ width: `${progress}%` }} />
            </div>
            <span>
              {done.size} of {posts.length} done
            </span>
          </div>

          {post && (
            <PostCard
              key={post.id}
              post={post}
              onDone={(correct) => markDone(post.id, correct)}
              finished={done.has(post.id)}
            />
          )}

          {atEnd && (
            <section className={`feed__end${allDone ? ' is-complete' : ''}`}>
              {allDone ? (
                <p>All {posts.length} done. 🎉</p>
              ) : (
                <p>
                  {done.size} of {posts.length} done. Go back to finish the rest.
                </p>
              )}
            </section>
          )}

          {posts.length > 0 && (
            <nav className="feed-panel__nav">
              <button disabled={current === 0} onClick={() => setIndex(current - 1)}>
                ← Back
              </button>
              <span>
                {Math.min(current + 1, posts.length)} / {posts.length}
              </span>
              <button disabled={atEnd} onClick={() => setIndex(current + 1)}>
                Next →
              </button>
            </nav>
          )}

          <a className="feed-panel__full" href={`/?feed=${paperId}`} target="_blank" rel="noreferrer">
            Full screen ↗
          </a>
        </>
      )}
    </div>
  )
}
