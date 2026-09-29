import { useCallback, useEffect, useRef, useState } from 'react'

import { useHeardTracker } from '../progress/useHeardTracker'
import { Fullscreen } from '../reader/Fullscreen'
import { fetchStoryboard, narrationState, narrationUrl, startNarration } from './api'
import type { NarrationState, Storyboard } from './types'
import { VideoPlayer } from './VideoPlayer'
import './video.css'

const NARRATION_POLL_MS = 5000

type Props = {
  paperId: string
}

/** The explainer video inside the reader's side column, with full screen. */
export function VideoWidget({ paperId }: Props) {
  const [board, setBoard] = useState<Storyboard | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [narration, setNarration] = useState<NarrationState | null>(null)
  const [fullscreen, setFullscreen] = useState(false)
  const opener = useRef<HTMLButtonElement>(null)
  const track = useHeardTracker(paperId, 'video')

  useEffect(() => {
    let active = true
    fetchStoryboard(paperId)
      .then((result) => active && setBoard(result))
      .catch((err) => active && setError(err instanceof Error ? err.message : 'Failed.'))
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

  const closeFullscreen = useCallback(() => {
    setFullscreen(false)
    opener.current?.focus()
  }, [])

  if (error) return <p className="analogy__error">{error}</p>
  if (!board) return <p className="analogy__status">Writing the video… about half a minute.</p>

  const ready = narration?.status === 'ready' ? narration.narration : null

  return (
    <div className="video-widget">
      <div className="video-widget__bar">
        <span className="video-widget__title">{board.title}</span>
        <button
          ref={opener}
          className="video-widget__expand"
          onClick={() => setFullscreen(true)}
          aria-label="Watch full screen"
          title="Full screen"
        >
          ⛶
        </button>
      </div>

      <Fullscreen open={fullscreen} title={board.title} onClose={closeFullscreen}>
        <VideoPlayer
          // A fresh player when the audio arrives, so its clock starts clean.
          key={ready ? 'narrated' : 'silent'}
          board={board}
          narration={ready}
          audioUrl={ready ? narrationUrl(paperId) : undefined}
          onPlayed={track}
        />
      </Fullscreen>

      {narration && narration.status !== 'ready' && (
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
    </div>
  )
}
