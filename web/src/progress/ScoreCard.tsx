import { useEffect, useState } from 'react'

import { fetchAssessment, requestAssessment } from './api'
import { notifyProgress } from './events'
import type { Assessment, Place } from './types'

const PLACE_LABEL: Record<Place, string> = {
  reading: 'Reading',
  feed: 'Learning feed',
  check: 'Check your understanding',
  podcast: 'Podcast',
  video: 'Explainer video',
  map: 'Knowledge map',
  summary: 'Paper in 3 lines',
}

type Props = {
  paperId: string
  onGo: (place: Place) => void
}

/** The agent's score of the user's understanding, and what to work on. */
export function ScoreCard({ paperId, onGo }: Props) {
  const [assessment, setAssessment] = useState<Assessment | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    fetchAssessment(paperId)
      .then((result) => active && setAssessment(result))
      .catch(() => {})
    return () => {
      active = false
    }
  }, [paperId])

  async function handleScore() {
    setLoading(true)
    setError(null)
    try {
      setAssessment(await requestAssessment(paperId))
      // The map colors the concepts the score names.
      notifyProgress()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scoring failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="score">
      {assessment && (
        <>
          <div className="score__head">
            <span className="score__value">{assessment.score}</span>
            <span className="score__of">/ 100</span>
            <p className="score__verdict">{assessment.verdict}</p>
          </div>

          {assessment.strengths.length > 0 && (
            <ul className="score__list score__list--good">
              {assessment.strengths.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          )}

          {assessment.improvements.length > 0 && (
            <>
              <p className="score__label">To improve</p>
              <ul className="score__list score__list--todo">
                {assessment.improvements.map((item, index) => (
                  <li key={index}>
                    {item.concept && <strong>{item.concept}: </strong>}
                    {item.why}{' '}
                    <button className="score__go" onClick={() => onGo(item.place)}>
                      {PLACE_LABEL[item.place]} →
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}

          <p className="score__date">
            Scored {new Date(assessment.created_at).toLocaleString()}
          </p>
        </>
      )}

      {error && <p className="analogy__error">{error}</p>}
      <button className="podcast__button" onClick={handleScore} disabled={loading}>
        {loading ? 'Scoring your understanding…' : assessment ? 'Update my score' : 'Get my score'}
      </button>
    </div>
  )
}
