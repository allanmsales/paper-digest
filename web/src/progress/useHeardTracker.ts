import { useCallback, useEffect, useRef } from 'react'

import { reportHeard } from './api'
import { notifyProgress } from './events'
import type { MediaKind } from './types'

const BUCKET_SECONDS = 5
const FLUSH_MS = 5000

/** Records which 5-second parts of a recording were actually played, so
 *  skipping ahead doesn't count. Call `track` with the time while playing. */
export function useHeardTracker(paperId: string, kind: MediaKind) {
  const pending = useRef(new Set<number>())
  const sent = useRef(new Set<number>())
  const total = useRef(0)

  const flush = useCallback(() => {
    if (!pending.current.size || !total.current) return
    const buckets = [...pending.current]
    pending.current.clear()
    buckets.forEach((bucket) => sent.current.add(bucket))
    reportHeard(paperId, kind, buckets, total.current)
      .then(notifyProgress)
      .catch(() =>
        // Not saved: queue them again for the next flush.
        buckets.forEach((bucket) => {
          sent.current.delete(bucket)
          pending.current.add(bucket)
        }),
      )
  }, [paperId, kind])

  useEffect(() => {
    const timer = window.setInterval(flush, FLUSH_MS)
    return () => {
      window.clearInterval(timer)
      flush()
    }
  }, [flush])

  return useCallback((time: number, duration: number) => {
    if (!Number.isFinite(duration) || duration <= 0) return
    total.current = Math.ceil(duration / BUCKET_SECONDS)
    const bucket = Math.min(Math.floor(time / BUCKET_SECONDS), total.current - 1)
    if (!sent.current.has(bucket)) pending.current.add(bucket)
  }, [])
}
