import { useEffect, useState } from 'react'

import { listLibrary, type LibraryEntry } from './api'
import type { PdfSource } from './types'

type Props = {
  onOpen: (source: PdfSource) => void
}

function isUrl(source: string | null): source is string {
  return !!source && /^https?:\/\//.test(source)
}

/** Papers this user opened before, most recent first. */
export function LibraryList({ onOpen }: Props) {
  const [entries, setEntries] = useState<LibraryEntry[] | null>(null)

  useEffect(() => {
    listLibrary()
      .then(setEntries)
      .catch(() => setEntries([]))
  }, [])

  if (!entries?.length) return null

  return (
    <section className="library">
      <h2>Continue reading</h2>
      <ul>
        {entries.map((entry) => (
          <li key={entry.paper_id}>
            {isUrl(entry.source) ? (
              <button onClick={() => onOpen({ kind: 'url', url: entry.source! })}>
                {entry.source}
              </button>
            ) : (
              <span title="Only the text is stored: upload the PDF again to reopen it.">
                {entry.source ?? 'Uploaded PDF'} <em>· upload again</em>
              </span>
            )}
            <time dateTime={entry.last_opened}>
              {new Date(entry.last_opened).toLocaleDateString()}
            </time>
          </li>
        ))}
      </ul>
    </section>
  )
}
