import { useState } from 'react'

import { confirmMilestone } from '../progress/api'
import { notifyProgress } from '../progress/events'
import type { Progress } from '../progress/types'

type Props = {
  paperId: string
  progress: Progress | null
  pageCount: number
}

/** Step 1: read the paper. Pages count as you look at them; you can also
 *  confirm you read it. */
export function ReadingPanel({ paperId, progress, pageCount }: Props) {
  const [saving, setSaving] = useState(false)
  const confirmed = progress?.confirmed.includes('reading') ?? false
  const share = progress?.reading ?? 0
  const pagesRead = confirmed ? null : Math.round(share * pageCount)

  function handleConfirm() {
    setSaving(true)
    confirmMilestone(paperId, 'reading')
      .then(notifyProgress)
      .catch(() => {})
      .finally(() => setSaving(false))
  }

  return (
    <div className="reading">
      <p className="reading__hint">
        Start by reading the paper on the left. Take your time; the other steps help with what
        is unclear.
      </p>
      {pagesRead !== null && pageCount > 0 && (
        <div className="reading__pages">
          <span className="progress__bar" aria-hidden>
            <span style={{ width: `${Math.round(share * 100)}%` }} />
          </span>
          <span>
            {pagesRead} of {pageCount} pages read
          </span>
        </div>
      )}
      {confirmed ? (
        <p className="reading__done">✓ You've read the paper</p>
      ) : (
        <button className="podcast__button" onClick={handleConfirm} disabled={saving}>
          I've read the paper
        </button>
      )}
    </div>
  )
}
