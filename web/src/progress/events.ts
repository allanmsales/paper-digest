import { useEffect, useState } from 'react'

import { fetchProgress } from './api'
import type { Progress } from './types'

const EVENT = 'pd:progress'
const REFRESH_DELAY_MS = 400

/** Tells every progress view to refetch: call after anything that counts. */
export function notifyProgress(): void {
  window.dispatchEvent(new Event(EVENT))
}

/** The user's progress on a paper, refreshed whenever something counts. */
export function useProgress(paperId: string | null): Progress | null {
  const [progress, setProgress] = useState<Progress | null>(null)

  useEffect(() => {
    if (!paperId) return
    let active = true
    let timer = 0
    const load = () => {
      fetchProgress(paperId)
        .then((result) => active && setProgress(result))
        .catch(() => {})
    }
    // Several updates in a row (e.g. media ticks) cost one request.
    const onChange = () => {
      window.clearTimeout(timer)
      timer = window.setTimeout(load, REFRESH_DELAY_MS)
    }
    load()
    window.addEventListener(EVENT, onChange)
    return () => {
      active = false
      window.clearTimeout(timer)
      window.removeEventListener(EVENT, onChange)
    }
  }, [paperId])

  return paperId ? progress : null
}
