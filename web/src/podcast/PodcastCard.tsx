import { useEffect, useState } from 'react'

import { audioStatus, audioUrl, generateAudio, podcastScript } from './api'
import type { AudioStatus, Script } from './types'
import './podcast.css'

const POLL_MS = 5000

type Props = {
  paperId: string
}

/** An interview with the "author", voiced locally: listen instead of read. */
export function PodcastCard({ paperId }: Props) {
  const [status, setStatus] = useState<AudioStatus | null>(null)
  const [script, setScript] = useState<Script | null>(null)
  const [showTranscript, setShowTranscript] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    audioStatus(paperId)
      .then((result) => {
        if (!active) return
        setStatus(result.status)
        setError(result.detail)
      })
      .catch((err) => active && setError(err instanceof Error ? err.message : 'Failed.'))
    return () => {
      active = false
    }
  }, [paperId])

  useEffect(() => {
    if (status !== 'running') return
    const timer = setInterval(() => {
      audioStatus(paperId)
        .then((result) => {
          setStatus(result.status)
          setError(result.detail)
        })
        .catch(() => {})
    }, POLL_MS)
    return () => clearInterval(timer)
  }, [paperId, status])

  // The script exists once the audio is ready, so this is instant.
  useEffect(() => {
    if (status !== 'ready' || script) return
    podcastScript(paperId)
      .then(setScript)
      .catch(() => {})
  }, [paperId, status, script])

  function handleGenerate() {
    setError(null)
    setStatus('running')
    generateAudio(paperId)
      .then(setStatus)
      .catch((err) => {
        setStatus('failed')
        setError(err instanceof Error ? err.message : 'Failed.')
      })
  }

  return (
    <section className="podcast">
      <header className="podcast__header">
        <h3>{script?.title ?? 'Podcast'}</h3>
      </header>

      {error && <p className="analogy__error">{error}</p>}

      {(status === 'none' || status === 'failed') && (
        <>
          <p className="podcast__hint">
            {status === 'failed'
              ? 'The last try failed.'
              : 'Hear the author explain the paper in a short interview.'}
          </p>
          <button className="podcast__button" onClick={handleGenerate}>
            {status === 'failed' ? 'Try again' : 'Make podcast'}
          </button>
        </>
      )}

      {status === 'running' && (
        <p className="analogy__status">Recording the episode… a few minutes.</p>
      )}

      {status === 'ready' && (
        <>
          <audio className="podcast__player" controls preload="metadata" src={audioUrl(paperId)} />
          {script && (
            <button
              className="podcast__link"
              onClick={() => setShowTranscript((value) => !value)}
              aria-expanded={showTranscript}
            >
              {showTranscript ? 'Hide transcript' : 'Show transcript'}
            </button>
          )}
          {showTranscript && script && (
            <dl className="podcast__transcript">
              {script.lines.map((line, index) => (
                <div key={index} className="podcast__line">
                  <dt>{line.speaker === 'host' ? 'Host' : 'Author'}</dt>
                  <dd>{line.text}</dd>
                </div>
              ))}
            </dl>
          )}
        </>
      )}
    </section>
  )
}
