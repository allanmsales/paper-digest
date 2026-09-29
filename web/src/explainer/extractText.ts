import type { PDFDocumentProxy } from 'pdfjs-dist'

/** Full text with page markers, matching the backend's PDF parser format. */
export async function extractPaperText(pdf: PDFDocumentProxy): Promise<string> {
  const pages: string[] = []

  for (let number = 1; number <= pdf.numPages; number++) {
    const page = await pdf.getPage(number)
    const content = await page.getTextContent()
    const text = content.items
      .map((item) => ('str' in item ? item.str + (item.hasEOL ? '\n' : '') : ''))
      .join('')
    if (text.trim()) pages.push(`--- PAGE ${number} ---\n${text}`)
  }

  return pages.join('\n\n')
}
