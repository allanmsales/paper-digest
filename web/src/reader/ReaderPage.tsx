import { useCallback, useState } from 'react'
import type { PDFDocumentProxy } from 'pdfjs-dist'

import { warmPaper } from '../explainer/api'
import { startFeedBuild } from '../feed/api'
import { CheckCard } from '../explainer/CheckCard'
import { ExplainPopover } from '../explainer/ExplainPopover'
import { extractPaperText } from '../explainer/extractText'
import { LookupsPanel } from '../explainer/LookupsPanel'
import { SummaryCard } from '../explainer/SummaryCard'
import type { Explanation, Lookup } from '../explainer/types'
import { useTextSelection } from '../explainer/useTextSelection'
import '../explainer/explainer.css'
import { PdfSourceForm } from './PdfSourceForm'
import { PdfViewer } from './PdfViewer'
import { pdfSourceLabel, type PdfSource } from './types'
import './reader.css'

export function ReaderPage() {
  const [source, setSource] = useState<PdfSource | null>(null)
  // Bumped on every open so the viewer remounts with fresh state.
  const [openCount, setOpenCount] = useState(0)
  const [paperText, setPaperText] = useState<string | null>(null)
  const [paperId, setPaperId] = useState<string | null>(null)
  const [lookups, setLookups] = useState<Lookup[]>([])
  const [guessFirst, setGuessFirst] = useState(false)
  const [showCheck, setShowCheck] = useState(false)
  const { selected, onMouseUp, clear } = useTextSelection()

  function handleOpen(next: PdfSource) {
    setSource(next)
    setOpenCount((count) => count + 1)
    setPaperText(null)
    setPaperId(null)
    setLookups([])
    setShowCheck(false)
    clear()
  }

  const sourceLabel = source ? pdfSourceLabel(source) : ''

  const handleDocumentLoad = useCallback(
    async (pdf: PDFDocumentProxy) => {
      const text = await extractPaperText(pdf)
      setPaperText(text)
      const id = await warmPaper(text, sourceLabel)
      setPaperId(id)
      // The feed takes a few minutes to prepare; start it right away.
      if (id) startFeedBuild(id)
    },
    [sourceLabel],
  )

  function handleExplained(params: { guess: string | null; result: Explanation }) {
    if (!selected) return
    setLookups((current) => [
      { id: Date.now(), selection: selected.text, ...params },
      ...current,
    ])
  }

  return (
    <div className="reader">
      <header className="reader__header">
        <h1>Paper Digest</h1>
        <PdfSourceForm onOpen={handleOpen} />
        <button
          className="reader__summary-button"
          disabled={!paperText}
          onClick={() => setShowCheck(true)}
          title={paperText ? undefined : 'Open a paper first'}
        >
          Check
        </button>
        {paperId && (
          <a
            className="reader__summary-button"
            href={`/?feed=${paperId}`}
            target="_blank"
            rel="noreferrer"
          >
            Learn in the feed ↗
          </a>
        )}
        <label className="reader__toggle">
          <input
            type="checkbox"
            checked={guessFirst}
            onChange={(event) => setGuessFirst(event.target.checked)}
          />
          Guess first
        </label>
      </header>

      {source ? (
        <main className="reader__main reader__main--open">
          <div className="reader__document" onMouseUp={onMouseUp}>
            <p className="reader__current" title={pdfSourceLabel(source)}>
              {pdfSourceLabel(source)}
            </p>
            <PdfViewer
              key={openCount}
              source={source}
              onDocumentLoad={handleDocumentLoad}
            />
          </div>
          <div className="reader__side">
            {paperText && <SummaryCard paperText={paperText} />}
            {showCheck && paperText && (
              <CheckCard paperText={paperText} onClose={() => setShowCheck(false)} />
            )}
            <LookupsPanel lookups={lookups} paperText={paperText} />
          </div>
        </main>
      ) : (
        <main className="reader__main">
          <p className="reader__empty">
            Open a paper by URL or upload a PDF to start reading.
          </p>
        </main>
      )}

      {selected && (
        <ExplainPopover
          key={`${selected.text}-${selected.rect.top}-${selected.rect.left}`}
          selected={selected}
          paperText={paperText}
          guessFirst={guessFirst}
          onExplained={handleExplained}
          onClose={clear}
        />
      )}
    </div>
  )
}
