import { PostCard } from './PostCard'
import { useFeedSession } from './useFeedSession'
import './feed.css'

type Props = {
  paperId: string
}

const scrollToTop = () => window.scrollTo({ top: 0 })

/** A short, finite feed of posts about the paper's prerequisites. */
export function FeedPage({ paperId }: Props) {
  const { session, posts, done, error, markDone, allDone, progress } = useFeedSession(
    paperId,
    scrollToTop,
  )

  return (
    <div className="feed">
      <header className="feed__header">
        <h1>Learning feed</h1>
        {session?.status === 'ready' && (
          <div className="feed__progress" title={`${progress}% done`}>
            <div className="feed__bar">
              <div style={{ width: `${progress}%` }} />
            </div>
            <span>
              {done.size} of {posts.length} done
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
            onDone={(correct) => markDone(post.id, correct)}
            finished={done.has(post.id)}
          />
        ))}

        {session?.status === 'ready' && (
          <section className={`feed__end${allDone ? ' is-complete' : ''}`}>
            {allDone ? (
              <p>All {posts.length} done. 🎉</p>
            ) : (
              <p>
                {done.size} of {posts.length} done.
              </p>
            )}
          </section>
        )}
      </main>
    </div>
  )
}
