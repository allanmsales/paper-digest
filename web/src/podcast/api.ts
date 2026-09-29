import type { AudioStatus, Script } from './types'

async function request<T>(method: 'GET' | 'POST', path: string): Promise<T> {
  const response = await fetch(`/api/podcast/${path}`, { method })

  if (!response.ok) {
    const data = await response.json().catch(() => null)
    const detail =
      typeof data?.detail === 'string' ? data.detail : `Request failed (${response.status}).`
    throw new Error(detail)
  }

  return response.json()
}

export type AudioState = { status: AudioStatus; detail: string | null }

export function audioStatus(paperId: string): Promise<AudioState> {
  return request('GET', `${paperId}/status`)
}

/** Starts writing and voicing the episode; it takes a few minutes. */
export async function generateAudio(paperId: string): Promise<AudioStatus> {
  const { status } = await request<{ status: AudioStatus }>('POST', `${paperId}/audio`)
  return status
}

export function podcastScript(paperId: string): Promise<Script> {
  return request('POST', `${paperId}/script`)
}

export function audioUrl(paperId: string): string {
  return `/api/podcast/${paperId}/audio.mp3`
}
