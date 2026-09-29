import { useEffect, useState, type FormEvent } from 'react'

import { checkUnderstanding, listChecks, summarize } from './api'
import { AskThread } from './AskThread'
import { notifyProgress } from '../progress/events'
import type { CheckResult, PaperSection } from './types'

const LEVEL_LABEL: Record<CheckResult['level'], string> = {
  got_it: 'Got it',
  partly: 'Partly',
  not_yet: 'Not yet',
}

type Attempt = { answer: string; result: CheckResult }

type Props = {
  paperText: string
  paperId: string | null
}

/** Section by section, the reader writes what they understood; each
 *  answer is graded against that section's key ideas. */
export function CheckCard({ paperText, paperId }: Props) {
  const [sections, setSections] = useState<PaperSection[] | null>(null)
  const [current, setCurrent] = useState(0)
  const [attempts, setAttempts] = useState<Record<number, Attempt[]>>({})
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    // Instant: the summary (with sections) is prepared during warm-up.
    summarize(paperText)
      .then((summary) => active && setSections(summary.sections))
      .catch((err) => active && setError(err instanceof Error ? err.message : 'Failed.'))
    return () => {
      active = false
    }
  }, [paperText])

  // Earlier answers, so the path and history survive a reload.
  useEffect(() => {
    if (!paperId) return
    let active = true
    listChecks(paperId)
      .then((saved) => {
        if (!active) return
        const grouped: Record<number, Attempt[]> = {}
        for (const { section, answer, result } of saved) {
          ;(grouped[section] ??= []).push({ answer, result })
        }
        setAttempts(grouped)
      })
      .catch(() => {})
    return () => {
      active = false
    }
  }, [paperId])

  const sectionAttempts = attempts[current] ?? []
  const latest = sectionAttempts[0]
  const section = sections?.[current]
  const next = sections && current + 1 < sections.length ? current + 1 : null

  function select(index: number) {
    setCurrent(index)
    setAnswer('')
    setError(null)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const text = answer.trim()
    if (!text) return
    setLoading(true)
    setError(null)
    try {
      const result = await checkUnderstanding(paperText, current, text)
      setAttempts((all) => ({
        ...all,
        [current]: [{ answer: text, result }, ...(all[current] ?? [])],
      }))
      setAnswer('')
      notifyProgress()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="check">

      {!sections && !error && <p className="analogy__status">Loading sections…</p>}

      {sections && (
        <ol className="check__path">
          {sections.map((item, index) => {
            const level = attempts[index]?.[0]?.result.level
            return (
              <li key={item.title}>
                <button
                  className={index === current ? 'is-current' : undefined}
                  onClick={() => select(index)}
                  title={`Page ${item.page}`}
                >
                  <span className={`check__dot${level ? ` check__dot--${level}` : ''}`} />
                  {item.title}
                </button>
              </li>
            )
          })}
        </ol>
      )}

      {latest && (
        <div className="check__result">
          <p className={`check__level check__level--${latest.result.level}`}>
            {LEVEL_LABEL[latest.result.level]}
          </p>
          <ul className="check__ideas">
            {latest.result.ideas.map((item) => (
              <li key={item.idea} className={item.covered ? 'is-covered' : 'is-missed'}>
                <span aria-hidden>{item.covered ? '✓' : '✗'}</span>
                <div>
                  {item.idea}
                  {!item.covered && item.reread_at && (
                    <span className="check__reread">Reread: {item.reread_at}</span>
                  )}
                  {!item.covered && (
                    <AskThread
                      paperText={paperText}
                      anchor={`Key idea of "${section?.title}" the reader missed: ${item.idea}`}
                    />
                  )}
                </div>
              </li>
            ))}
          </ul>
          {next !== null && latest.result.level !== 'not_yet' && (
            <button className="check__next" onClick={() => select(next)}>
              Next: {sections?.[next].title} →
            </button>
          )}
        </div>
      )}

      {section && (
        <form className="check__form" onSubmit={handleSubmit}>
          <label htmlFor="check-answer">
            {latest
              ? 'Try again in your own words:'
              : `After reading “${section.title}”, what did you understand? Use your own words.`}
          </label>
          <textarea
            id="check-answer"
            rows={4}
            value={answer}
            onChange={(event) => setAnswer(event.target.value)}
            placeholder="A few sentences are enough."
          />
          {error && <p className="analogy__error">{error}</p>}
          <button type="submit" disabled={loading || !answer.trim()}>
            {loading ? 'Checking…' : 'Check'}
          </button>
        </form>
      )}

      {sectionAttempts.length > 1 && (
        <details className="check__history">
          <summary>Previous attempts ({sectionAttempts.length - 1})</summary>
          <ul>
            {sectionAttempts.slice(1).map((attempt, index) => (
              <li key={index}>
                <strong>{LEVEL_LABEL[attempt.result.level]}</strong>: {attempt.answer}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  )
}
