import { useEffect, useState } from 'react'

import { explain } from './api'
import { ExplanationCard } from './ExplanationCard'
import type { Explanation, SelectedText } from './types'

const POPOVER_WIDTH = 320

type Stage =
  | { name: 'idle' }
  | { name: 'guessing' }
  | { name: 'loading' }
  | { name: 'done'; result: Explanation }
  | { name: 'error'; message: string }

type Props = {
  selected: SelectedText
  paperText: string | null
  guessFirst: boolean
  onExplained: (params: { guess: string | null; result: Explanation }) => void
  onClose: () => void
}

export function ExplainPopover({
  selected,
  paperText,
  guessFirst,
  onExplained,
  onClose,
}: Props) {
  const [stage, setStage] = useState<Stage>({ name: 'idle' })
  const [guess, setGuess] = useState('')

  useEffect(() => {
    function handleKey(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onClose])

  async function run(withGuess: string | null) {
    if (!paperText) return
    setStage({ name: 'loading' })
    try {
      const result = await explain({
        selection: selected.text,
        page: selected.page,
        paperText,
        guess: withGuess,
      })
      setStage({ name: 'done', result })
      onExplained({ guess: withGuess, result })
    } catch (err) {
      setStage({
        name: 'error',
        message: err instanceof Error ? err.message : 'Something went wrong.',
      })
    }
  }

  const left = Math.max(
    16,
    Math.min(selected.rect.left, window.innerWidth - POPOVER_WIDTH - 16),
  )
  const expanded = stage.name !== 'idle'

  return (
    <div
      className={`explain-popover${expanded ? ' explain-popover--expanded' : ''}`}
      style={{ top: selected.rect.bottom + 8, left }}
      onMouseUp={(event) => event.stopPropagation()}
    >
      {stage.name === 'idle' && (
        <button
          className="explain-popover__trigger"
          disabled={!paperText}
          title={paperText ? undefined : 'Still reading the paper text…'}
          onClick={() => (guessFirst ? setStage({ name: 'guessing' }) : run(null))}
        >
          Explain
        </button>
      )}

      {expanded && (
        <>
          <header className="explain-popover__header">
            <strong>“{selected.text}”</strong>
            <button className="explain-popover__close" onClick={onClose} aria-label="Close">
              ×
            </button>
          </header>

          <div className="explain-popover__body">
            {stage.name === 'guessing' && (
              <form
                className="explain-popover__guess"
                onSubmit={(event) => {
                  event.preventDefault()
                  run(guess.trim() || null)
                }}
              >
                <label htmlFor="guess">What do you think it means?</label>
                <textarea
                  id="guess"
                  rows={3}
                  autoFocus
                  value={guess}
                  onChange={(event) => setGuess(event.target.value)}
                  placeholder="One line is enough."
                />
                <div className="explain-popover__actions">
                  <button type="button" className="link" onClick={() => run(null)}>
                    Skip
                  </button>
                  <button type="submit" disabled={!guess.trim()}>
                    Check my guess
                  </button>
                </div>
              </form>
            )}

            {stage.name === 'loading' && (
              <p className="explain-popover__status">Clarifying…</p>
            )}

            {stage.name === 'error' && (
              <p className="explain-popover__error">{stage.message}</p>
            )}

            {stage.name === 'done' && (
              <ExplanationCard
                result={stage.result}
                subject={selected.text}
                paperText={paperText}
              />
            )}
          </div>
        </>
      )}
    </div>
  )
}
