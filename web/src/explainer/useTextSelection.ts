import { useCallback, useState } from 'react'

import type { SelectedText } from './types'

// Matches the backend limit.
const MAX_SELECTION_LENGTH = 2000

/** Captures the text selected inside the element that receives `onMouseUp`. */
export function useTextSelection() {
  const [selected, setSelected] = useState<SelectedText | null>(null)

  const onMouseUp = useCallback((event: React.MouseEvent<HTMLElement>) => {
    const selection = window.getSelection()
    const text = selection?.toString().replace(/\s+/g, ' ').trim() ?? ''

    if (!selection || !text || text.length > MAX_SELECTION_LENGTH) {
      setSelected(null)
      return
    }

    const range = selection.getRangeAt(0)
    if (!event.currentTarget.contains(range.commonAncestorContainer)) return

    const rect = range.getBoundingClientRect()
    const page = range.startContainer.parentElement?.closest('.react-pdf__Page')
    const pageNumber = Number(page?.getAttribute('data-page-number'))

    setSelected({
      text,
      page: pageNumber || null,
      // Document coordinates, so the popover scrolls with the paper.
      rect: {
        top: rect.top + window.scrollY,
        left: rect.left + window.scrollX,
        bottom: rect.bottom + window.scrollY,
      },
    })
  }, [])

  const clear = useCallback(() => setSelected(null), [])

  return { selected, onMouseUp, clear }
}
