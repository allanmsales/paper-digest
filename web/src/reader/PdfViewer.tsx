import { useEffect, useRef, useState } from 'react'
import type { PDFDocumentProxy } from 'pdfjs-dist'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'

import type { PdfSource } from './types'

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

const MAX_PAGE_WIDTH = 900
// A page counts as read after half of it stayed on screen this long.
const PAGE_READ_MS = 5000

type Props = {
  source: PdfSource
  onDocumentLoad?: (pdf: PDFDocumentProxy) => void
  /** Called once per page the reader looked at long enough. */
  onPageRead?: (pageIndex: number, pageCount: number) => void
}

export function PdfViewer({ source, onDocumentLoad, onPageRead }: Props) {
  const [numPages, setNumPages] = useState(0)
  const { file, error: fetchError } = usePdfFile(source)
  const [renderError, setRenderError] = useState<string | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const pageWidth = useContainerWidth(containerRef, MAX_PAGE_WIDTH)

  const error = fetchError ?? renderError
  usePageReadTracker(containerRef, numPages, onPageRead)

  return (
    <div className="pdf-viewer" ref={containerRef}>
      {error ? (
        <p className="pdf-viewer__error">{error}</p>
      ) : !file ? (
        <p className="pdf-viewer__status">Downloading PDF…</p>
      ) : (
        <Document
          file={file}
          onLoadSuccess={(pdf) => {
            setNumPages(pdf.numPages)
            onDocumentLoad?.(pdf)
          }}
          onLoadError={(loadError) =>
            setRenderError(loadError.message || 'Could not read this PDF.')
          }
          loading={<p className="pdf-viewer__status">Loading PDF…</p>}
          error={null}
        >
          {Array.from({ length: numPages }, (_, index) => (
            <div className="pdf-viewer__page" key={index} data-page-index={index}>
              <Page pageNumber={index + 1} width={pageWidth} />
              <span className="pdf-viewer__page-number">
                {index + 1} / {numPages}
              </span>
            </div>
          ))}
        </Document>
      )}
    </div>
  )
}

/**
 * Resolves the source to a Blob. URLs go through the backend proxy so we can
 * show its error message instead of a generic pdf.js failure.
 */
function usePdfFile(source: PdfSource): {
  file: Blob | null
  error: string | null
} {
  const [state, setState] = useState<{ file: Blob | null; error: string | null }>(
    () => ({ file: source.kind === 'file' ? source.file : null, error: null }),
  )

  useEffect(() => {
    if (source.kind === 'file') return

    const controller = new AbortController()

    async function load(url: string) {
      try {
        const response = await fetch(
          `/api/reader/pdf?url=${encodeURIComponent(url)}`,
          { signal: controller.signal },
        )
        if (!response.ok) {
          const body = await response.json().catch(() => null)
          throw new Error(body?.detail ?? `Request failed (${response.status}).`)
        }
        setState({ file: await response.blob(), error: null })
      } catch (err) {
        if (controller.signal.aborted) return
        setState({
          file: null,
          error: err instanceof Error ? err.message : 'Could not load the PDF.',
        })
      }
    }

    load(source.url)
    return () => controller.abort()
  }, [source])

  return state
}

function usePageReadTracker(
  ref: React.RefObject<HTMLElement | null>,
  numPages: number,
  onPageRead?: (pageIndex: number, pageCount: number) => void,
) {
  const callback = useRef(onPageRead)
  useEffect(() => {
    callback.current = onPageRead
  }, [onPageRead])

  useEffect(() => {
    const root = ref.current
    if (!root || !numPages) return
    const timers = new Map<number, number>()
    const read = new Set<number>()

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const index = Number((entry.target as HTMLElement).dataset.pageIndex)
          if (read.has(index)) continue
          if (entry.isIntersecting) {
            if (timers.has(index)) continue
            timers.set(
              index,
              window.setTimeout(() => {
                read.add(index)
                timers.delete(index)
                observer.unobserve(entry.target)
                callback.current?.(index, numPages)
              }, PAGE_READ_MS),
            )
          } else {
            window.clearTimeout(timers.get(index))
            timers.delete(index)
          }
        }
      },
      { threshold: 0.5 },
    )
    root.querySelectorAll('[data-page-index]').forEach((page) => observer.observe(page))
    return () => {
      observer.disconnect()
      timers.forEach((timer) => window.clearTimeout(timer))
    }
  }, [ref, numPages])
}

function useContainerWidth(
  ref: React.RefObject<HTMLElement | null>,
  max: number,
): number {
  const [width, setWidth] = useState(max)

  useEffect(() => {
    const element = ref.current
    if (!element) return

    const observer = new ResizeObserver(([entry]) => {
      setWidth(Math.min(entry.contentRect.width, max))
    })
    observer.observe(element)
    return () => observer.disconnect()
  }, [ref, max])

  return width
}
