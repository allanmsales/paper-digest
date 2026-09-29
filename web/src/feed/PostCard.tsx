import { useState } from 'react'

import type { FeedPost } from './types'

type Props = {
  post: FeedPost
  onDone: (correct: boolean | null) => void
  /** Finished earlier: shown as done. */
  finished?: boolean
}

/** One post. The reader finishes it by reading, flipping or answering. */
export function PostCard({ post, onDone, finished = false }: Props) {
  const [flipped, setFlipped] = useState(false)
  const [picked, setPicked] = useState<number | null>(null)
  const [done, setDone] = useState(finished)

  function finish(correct: boolean | null) {
    if (done) return
    setDone(true)
    onDone(correct)
  }

  function pick(index: number) {
    if (picked !== null) return
    setPicked(index)
    finish(index === post.answer_index)
  }

  return (
    <article className={`post post--${post.kind}${done ? ' is-done' : ''}`}>
      <p className="post__concept">#{post.concept}</p>
      <h2 className="post__title">{post.title}</h2>
      <p className="post__body">{post.body}</p>

      {post.kind === 'flip' &&
        (flipped ? (
          <p className="post__back">{post.back}</p>
        ) : (
          <button className="post__action" onClick={() => setFlipped(true)}>
            Flip ↻
          </button>
        ))}

      {post.kind === 'quiz' && (
        <ul className="post__options">
          {post.options.map((option, index) => {
            const state =
              picked === null
                ? ''
                : index === post.answer_index
                  ? ' is-right'
                  : index === picked
                    ? ' is-wrong'
                    : ''
            return (
              <li key={option}>
                <button
                  className={`post__option${state}`}
                  disabled={picked !== null}
                  onClick={() => pick(index)}
                >
                  {option}
                </button>
              </li>
            )
          })}
        </ul>
      )}

      {(post.kind !== 'quiz' || picked !== null) && (
        <p className="post__why">📄 {post.why_it_matters}</p>
      )}

      {post.kind !== 'quiz' && (post.kind === 'lesson' || flipped) && (
        <button className="post__action" disabled={done} onClick={() => finish(null)}>
          {done ? '✓ Done' : '✓ Got it'}
        </button>
      )}
    </article>
  )
}
