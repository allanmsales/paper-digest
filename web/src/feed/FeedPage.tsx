import { PostCard } from './PostCard'
import { useFeedSession } from './useFeedSession'
import './feed.css'

type Props = {
  paperId: string
}

const scrollToTop = () => window.scrollTo({ top: 0 })

/** A short, finite feed of posts about the paper's prerequisites. */
export function FeedPage({ paperId }: Props) {
  const { session, posts, done, error, load, markDone, allDone, progress } = useFeedSession(
    paperId,
    scrollToTop,
  )

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
            onDone={(correct) => markDone(post.id, correct)}
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
