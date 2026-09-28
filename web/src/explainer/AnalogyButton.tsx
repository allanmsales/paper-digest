import { useState } from 'react'

import { analogy } from './api'
import { Text } from './Text'
import type { Analogy } from './types'

type State =
  | { name: 'idle' }
  | { name: 'loading' }
  | { name: 'done'; result: Analogy }
  | { name: 'error'; message: string }

/** Everyday analogy on request, mapped back to the paper's terms. */
export function AnalogyButton({ paperText, subject }: { paperText: string; subject: string }) {
  const [state, setState] = useState<State>({ name: 'idle' })

  async function load() {
    setState({ name: 'loading' })
    try {
      setState({ name: 'done', result: await analogy(paperText, subject) })
    } catch (err) {
      setState({
        name: 'error',
        message: err instanceof Error ? err.message : 'Something went wrong.',
      })
    }
  }

  if (state.name === 'idle') {
    return (
      <button className="analogy__trigger" onClick={load}>
        💡 Analogy
      </button>
    )
  }

  if (state.name === 'loading') return <p className="analogy__status">Thinking of an analogy…</p>
  if (state.name === 'error') return <p className="analogy__error">{state.message}</p>

  return (
    <div className="analogy">
      <p>
        <Text>{state.result.analogy}</Text>
      </p>
      <ul className="analogy__mapping">
        {state.result.mapping.map((item) => (
          <li key={item.everyday}>
            {item.everyday} → <strong>{item.term}</strong>
          </li>
        ))}
      </ul>
    </div>
  )
}
