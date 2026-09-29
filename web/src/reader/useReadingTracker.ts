import { useCallback, useEffect, useRef } from 'react'

import { reportHeard } from '../progress/api'
import { notifyProgress } from '../progress/events'

/** Saves the pages the reader looked at. Pages read before the paper is
 *  registered (paperId still null) are kept and sent once it is. */
export function useReadingTracker(paperId: string | null) {
  const queued = useRef<{ pages: Set<number>; total: number }>({ pages: new Set(), total: 0 })

  const send = useCallback((id: string) => {
    const { pages, total } = queued.current
    if (!pages.size || !total) return
    const batch = [...pages]
    pages.clear()
    reportHeard(id, 'reading', batch, total)
      .then(notifyProgress)
      .catch(() => batch.forEach((page) => pages.add(page)))
  }, [])

  useEffect(() => {
    if (paperId) send(paperId)
  }, [paperId, send])

  return useCallback(
    (pageIndex: number, pageCount: number) => {
      queued.current.pages.add(pageIndex)
      queued.current.total = pageCount
      if (paperId) send(paperId)
    },
    [paperId, send],
  )
}
