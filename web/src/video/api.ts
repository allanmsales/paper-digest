import type { NarrationState, Storyboard } from './types'

/** Writes the storyboard on first call (about half a minute), then it's saved. */
export async function fetchStoryboard(paperId: string): Promise<Storyboard> {
  const response = await fetch(`/api/video/${paperId}/storyboard`, { method: 'POST' })
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    const detail =
      typeof data?.detail === 'string' ? data.detail : `Request failed (${response.status}).`
    throw new Error(detail)
  }
  return response.json()
}

async function request<T>(method: 'GET' | 'POST', path: string): Promise<T> {
  const response = await fetch(`/api/video/${path}`, { method })
  if (!response.ok) throw new Error(`Request failed (${response.status}).`)
  return response.json()
}

export function narrationState(paperId: string): Promise<NarrationState> {
  return request('GET', `${paperId}/narration`)
}

/** Starts recording the narration; it takes a few minutes. */
export function startNarration(paperId: string): Promise<NarrationState> {
  return request('POST', `${paperId}/narration`)
}

export function narrationUrl(paperId: string): string {
  return `/api/video/${paperId}/narration.mp3`
}
