import { useCallback, useEffect, useState, type ReactNode } from 'react'
import type { PDFDocumentProxy } from 'pdfjs-dist'

import { listLookups, warmPaper } from '../explainer/api'
import { startFeedBuild } from '../feed/api'
import { FeedPanel } from '../feed/FeedPanel'
import { CheckCard } from '../explainer/CheckCard'
import { ExplainPopover } from '../explainer/ExplainPopover'
import { extractPaperText } from '../explainer/extractText'
import { LookupsPanel } from '../explainer/LookupsPanel'
import { SummaryCard } from '../explainer/SummaryCard'
import type { Explanation, Lookup } from '../explainer/types'
import { useTextSelection } from '../explainer/useTextSelection'
import { PodcastCard } from '../podcast/PodcastCard'
import type { User } from '../users/types'
import { UserMenu } from '../users/UserMenu'
import '../users/users.css'
import '../explainer/explainer.css'
import { LibraryList } from './LibraryList'
import { PdfSourceForm } from './PdfSourceForm'
import { PdfViewer } from './PdfViewer'
import { SideSection } from './SideSection'
import { pdfSourceLabel, type PdfSource } from './types'
import './reader.css'

type Props = {
  user: User
}

type SectionId = 'summary' | 'feed' | 'check' | 'podcast' | 'lookups'

// Per-browser layout preferences; the page works without them.
function loadPref<T extends string>(key: string, fallback: T): T {
  try {
    return (localStorage.getItem(key) as T | null) ?? fallback
  } catch {
    return fallback
  }
}

function savePref(key: string, value: string) {
  try {
    localStorage.setItem(key, value)
  } catch {
    // Ignored: the preference just isn't remembered.
  }
}

export function ReaderPage({ user }: Props) {
  const [source, setSource] = useState<PdfSource | null>(null)
  // Bumped on every open so the viewer remounts with fresh state.
  const [openCount, setOpenCount] = useState(0)
  const [paperText, setPaperText] = useState<string | null>(null)
  const [paperId, setPaperId] = useState<string | null>(null)
  const [lookups, setLookups] = useState<Lookup[]>([])
  const [guessFirst, setGuessFirst] = useState(false)
  const [openSection, setOpenSection] = useState<SectionId | ''>(() =>
    loadPref<SectionId | ''>('pd.side.open', 'summary'),
  )
  const [folded, setFolded] = useState(() => loadPref('pd.side.folded', '') === '1')
  const { selected, onMouseUp, clear } = useTextSelection()

  function handleOpen(next: PdfSource) {
    setSource(next)
    setOpenCount((count) => count + 1)
    setPaperText(null)
    setPaperId(null)
    setLookups([])
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

  // Lookups are saved per user: reopening a paper brings them back.
  useEffect(() => {
    if (!paperId) return
    let active = true
    listLookups(paperId)
      .then((saved) => active && setLookups(saved))
      .catch(() => {})
    return () => {
      active = false
    }
  }, [paperId])

  function toggleSection(id: SectionId) {
    const next = openSection === id ? '' : id
    setOpenSection(next)
    savePref('pd.side.open', next)
  }

  function toggleFolded() {
    setFolded(!folded)
    savePref('pd.side.folded', folded ? '' : '1')
  }

  function section(id: SectionId, title: string, children: ReactNode, count?: number) {
    return (
      <SideSection
        title={title}
        count={count}
        open={openSection === id}
        onToggle={() => toggleSection(id)}
      >
        {children}
      </SideSection>
    )
  }

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
        <label className="reader__toggle">
          <input
            type="checkbox"
            checked={guessFirst}
            onChange={(event) => setGuessFirst(event.target.checked)}
          />
          Guess first
        </label>
        <UserMenu user={user} />
      </header>

      {source ? (
        <main className={`reader__main reader__main--open${folded ? ' reader__main--folded' : ''}`}>
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
          <div className={`reader__side${folded ? ' reader__side--folded' : ''}`}>
            <button
              className="reader__fold"
              onClick={toggleFolded}
              aria-label={folded ? 'Show side panel' : 'Hide side panel'}
              title={folded ? 'Show side panel' : 'Hide side panel'}
            >
              {folded ? '‹' : 'Hide ›'}
            </button>
            {!folded && (
              <>
                {section(
                  'summary',
                  'Paper in 3 lines',
                  paperText ? (
                    <SummaryCard paperText={paperText} />
                  ) : (
                    <p className="analogy__status">Reading the paper…</p>
                  ),
                )}
                {section(
                  'feed',
                  'Learning feed',
                  paperId ? (
                    <FeedPanel key={paperId} paperId={paperId} />
                  ) : (
                    <p className="analogy__status">Reading the paper…</p>
                  ),
                )}
                {section(
                  'check',
                  'Check your understanding',
                  paperText ? (
                    <CheckCard paperText={paperText} paperId={paperId} />
                  ) : (
                    <p className="analogy__status">Reading the paper…</p>
                  ),
                )}
                {section(
                  'podcast',
                  'Podcast',
                  paperId ? (
                    <PodcastCard key={paperId} paperId={paperId} />
                  ) : (
                    <p className="analogy__status">Reading the paper…</p>
                  ),
                )}
                {section(
                  'lookups',
                  'Your lookups',
                  <LookupsPanel lookups={lookups} paperText={paperText} />,
                  lookups.length,
                )}
              </>
            )}
          </div>
        </main>
      ) : (
        <main className="reader__main">
          <p className="reader__empty">
            Open a paper by URL or upload a PDF to start reading.
          </p>
          <LibraryList onOpen={handleOpen} />
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
