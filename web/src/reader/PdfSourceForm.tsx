import { useState, type FormEvent } from 'react'

import type { PdfSource } from './types'

type Props = {
  onOpen: (source: PdfSource) => void
}

export function PdfSourceForm({ onOpen }: Props) {
  const [url, setUrl] = useState('')

  function handleUrlSubmit(event: FormEvent) {
    event.preventDefault()
    const trimmed = url.trim()
    if (trimmed) onOpen({ kind: 'url', url: trimmed })
  }

  function handleFileChange(file: File | undefined) {
    if (file) onOpen({ kind: 'file', file })
  }

  return (
    <div className="source-form">
      <form className="source-form__url" onSubmit={handleUrlSubmit}>
        <input
          type="url"
          placeholder="Paste a PDF URL, e.g. https://arxiv.org/pdf/1706.03762"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          aria-label="PDF URL"
        />
        <button type="submit" disabled={!url.trim()}>
          Open
        </button>
      </form>

      <span className="source-form__or">or</span>

      <label className="source-form__upload">
        Upload PDF
        <input
          type="file"
          accept="application/pdf"
          onChange={(event) => {
            handleFileChange(event.target.files?.[0])
            event.target.value = ''
          }}
        />
      </label>
    </div>
  )
}
