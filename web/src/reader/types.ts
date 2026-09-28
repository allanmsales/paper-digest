export type PdfSource =
  | { kind: 'url'; url: string }
  | { kind: 'file'; file: File }

export function pdfSourceLabel(source: PdfSource): string {
  return source.kind === 'url' ? source.url : source.file.name
}
