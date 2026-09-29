export type LibraryEntry = {
  paper_id: string
  source: string | null
  last_opened: string
}

export async function listLibrary(): Promise<LibraryEntry[]> {
  const response = await fetch('/api/reader/library')
  if (!response.ok) throw new Error(`Request failed (${response.status}).`)
  return response.json()
}
