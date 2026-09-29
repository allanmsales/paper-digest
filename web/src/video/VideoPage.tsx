import { useEffect, useState } from 'react'

import { fetchStoryboard, narrationState, narrationUrl, startNarration } from './api'
import { StoryboardView } from './StoryboardView'
import type { NarrationState, Storyboard } from './types'
import { VideoPlayer } from './VideoPlayer'
import './video.css'

type Props = {
  paperId: string
}

const NARRATION_POLL_MS = 5000

/** The explainer video, with the static storyboard one click away. */
export function VideoPage({ paperId }: Props) {
  const [board, setBoard] = useState<Storyboard | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showStoryboard, setShowStoryboard] = useState(false)
  const [narration, setNarration] = useState<NarrationState | null>(null)

  useEffect(() => {
    let active = true
    fetchStoryboard(paperId)
      .then((result) => active && setBoard(result))
      .catch((err) => active && setError(err instanceof Error ? err.message : 'Failed.'))
    return () => {
      active = false
    }
  }, [paperId])

  useEffect(() => {
    let active = true
    narrationState(paperId)
      .then((state) => active && setNarration(state))
      .catch(() => {})
    return () => {
      active = false
    }
  }, [paperId])

  // Recording takes a few minutes: poll until it's done.
  useEffect(() => {
    if (narration?.status !== 'running') return
    const timer = window.setTimeout(() => {
      narrationState(paperId)
        .then(setNarration)
        .catch(() => {})
    }, NARRATION_POLL_MS)
    return () => window.clearTimeout(timer)
  }, [paperId, narration])

  function handleRecord() {
    setNarration({ status: 'running', detail: null, narration: null })
    startNarration(paperId)
      .then(setNarration)
      .catch((err) =>
        setNarration({
          status: 'failed',
          detail: err instanceof Error ? err.message : 'Failed.',
          narration: null,
        }),
      )
  }

  const ready = narration?.status === 'ready' ? narration.narration : null

  return (
    <div className="storyboard">
      <header className="storyboard__header">
        <a href="/">← Reader</a>
        <h1>{board?.title ?? 'Explainer video'}</h1>
        {board && (
          <button className="storyboard__toggle" onClick={() => setShowStoryboard(!showStoryboard)}>
            {showStoryboard ? 'Watch video' : 'All scenes'}
          </button>
        )}
      </header>

      <main className="storyboard__main">
        {error && <p className="storyboard__note storyboard__note--error">{error}</p>}
        {!board && !error && (
          <p className="storyboard__note">Writing the storyboard… about half a minute.</p>
        )}

        {board && !showStoryboard && narration && narration.status !== 'ready' && (
          <div className="narration-bar">
            {narration.status === 'running' ? (
              <span>Recording the narration… a few minutes. Captions play meanwhile.</span>
            ) : (
              <>
                <span>
                  {narration.status === 'failed'
                    ? narration.detail ?? 'Recording the narration failed.'
                    : 'Silent for now: captions only.'}
                </span>
                <button onClick={handleRecord}>
                  {narration.status === 'failed' ? 'Try again' : 'Add narration'}
                </button>
              </>
            )}
          </div>
        )}

        {board &&
          (showStoryboard ? (
            <StoryboardView board={board} />
          ) : (
            <VideoPlayer
              // A fresh player when the audio arrives, so its clock starts clean.
              key={ready ? 'narrated' : 'silent'}
              board={board}
              narration={ready}
              audioUrl={ready ? narrationUrl(paperId) : undefined}
            />
          ))}

        {board && (
          <section className="scene scene--check">
            <h2>Your turn</h2>
            <p>{board.check_question}</p>
          </section>
        )}
      </main>
    </div>
  )
}
