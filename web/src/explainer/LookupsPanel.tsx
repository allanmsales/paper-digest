import { ExplanationCard } from './ExplanationCard'
import type { Lookup } from './types'

type Props = {
  lookups: Lookup[]
  paperText: string | null
}

export function LookupsPanel({ lookups, paperText }: Props) {
  return (
    <aside className="lookups">
      <h3>Your lookups ({lookups.length})</h3>
      {lookups.length === 0 ? (
        <p className="lookups__empty">
          Select any text in the paper and click “Explain”. Everything you look up is kept
          here.
        </p>
      ) : (
        <ul>
          {lookups.map((lookup) => (
            <li key={lookup.id}>
              <details>
                <summary>{lookup.selection}</summary>
                {lookup.guess && (
                  <p className="lookups__guess">
                    Your guess: <em>{lookup.guess}</em>
                  </p>
                )}
                <ExplanationCard
                  result={lookup.result}
                  subject={lookup.selection}
                  paperText={paperText}
                />
              </details>
            </li>
          ))}
        </ul>
      )}
    </aside>
  )
}
