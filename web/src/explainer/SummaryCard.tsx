import { useEffect, useState } from 'react'

import { summarize } from './api'
import { AnalogyButton } from './AnalogyButton'
import { Text } from './Text'
import type { Summary } from './types'

type Props = {
  paperText: string
}

/** Problem / Idea / Result of the whole paper, prepared during warm-up. */
export function SummaryCard({ paperText }: Props) {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [minimized, setMinimized] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    summarize(paperText)
      .then((result) => active && setSummary(result))
      .catch((err) => active && setError(err instanceof Error ? err.message : 'Failed.'))
    return () => {
      active = false
    }
  }, [paperText])

  return (
    <section className="summary">
      <header className="summary__header">
        <h3>Paper in 3 lines</h3>
        <button
          className="summary__close"
          onClick={() => setMinimized((value) => !value)}
          aria-label={minimized ? 'Expand summary' : 'Minimize summary'}
          aria-expanded={!minimized}
        >
          {minimized ? '+' : '–'}
        </button>
      </header>

      {!minimized && error && <p className="analogy__error">{error}</p>}
      {!minimized && !summary && !error && <p className="analogy__status">Summarizing…</p>}

      {!minimized && summary && (
        <div className="explanation">
          <dl className="summary__lines">
            <dt>Problem</dt>
            <dd>
              <Text>{summary.problem}</Text>
            </dd>
            <dt>Idea</dt>
            <dd>
              <Text>{summary.idea}</Text>
            </dd>
            <dt>Result</dt>
            <dd>
              <Text>{summary.result}</Text>
            </dd>
          </dl>
          <AnalogyButton
            paperText={paperText}
            subject={`The paper's main idea: ${summary.idea}`}
          />
        </div>
      )}
    </section>
  )
}
