import { useCallback, useState } from 'react'

import { PostCard } from './PostCard'
import { useFeedSession } from './useFeedSession'
import './feed.css'

type Props = {
  paperId: string
}

/** The learning feed inside the reader's side column, one post at a time. */
export function FeedPanel({ paperId }: Props) {
  const [index, setIndex] = useState(0)
  const resetIndex = useCallback(() => setIndex(0), [])
  const { session, posts, done, error, load, markDone, allDone, progress } = useFeedSession(
    paperId,
    resetIndex,
  )

  const post = posts[index]
  const atEnd = index >= posts.length

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
          <div className="feed__progress" title={`${progress}% of concepts`}>
            <div className="feed__bar">
              <div style={{ width: `${progress}%` }} />
            </div>
            <span>
              {session.seen_concepts} of {session.total_concepts} concepts
            </span>
          </div>

          {post && (
            <PostCard
              key={post.id}
              post={post}
              onDone={(correct) => markDone(post.id, correct)}
            />
          )}

          {atEnd && (
            <section className={`feed__end${allDone ? ' is-complete' : ''}`}>
              {posts.length === 0 ? (
                <p>You’ve gone through every post for this paper. 🎉</p>
              ) : allDone ? (
                <p>Done for today. 🎉</p>
              ) : (
                <p>
                  {done.size} of {posts.length} done. Go back to finish the rest.
                </p>
              )}
              {session.remaining_posts > 0 && (
                <button onClick={load} disabled={!allDone}>
                  8 more
                </button>
              )}
            </section>
          )}

          {posts.length > 0 && (
            <nav className="feed-panel__nav">
              <button disabled={index === 0} onClick={() => setIndex(index - 1)}>
                ← Back
              </button>
              <span>
                {Math.min(index + 1, posts.length)} / {posts.length}
              </span>
              <button disabled={atEnd} onClick={() => setIndex(index + 1)}>
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
