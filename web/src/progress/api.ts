import type { Assessment, KnowledgeMapData, MediaKind, MilestoneItem, Progress } from './types'

export async function fetchProgress(paperId: string): Promise<Progress> {
  const response = await fetch(`/api/progress/${paperId}`)
  if (!response.ok) throw new Error(`Request failed (${response.status}).`)
  return response.json()
}

export async function reportHeard(
  paperId: string,
  kind: MediaKind,
  buckets: number[],
  total: number,
): Promise<void> {
  const response = await fetch(`/api/progress/${paperId}/heard`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ kind, buckets, total }),
  })
  if (!response.ok) throw new Error(`Request failed (${response.status}).`)
}

export async function fetchMap(paperId: string): Promise<KnowledgeMapData> {
  const response = await fetch(`/api/progress/${paperId}/map`)
  if (!response.ok) throw new Error(`Request failed (${response.status}).`)
  return response.json()
}

export async function fetchAssessment(paperId: string): Promise<Assessment | null> {
  const response = await fetch(`/api/progress/${paperId}/assessment`)
  if (!response.ok) throw new Error(`Request failed (${response.status}).`)
  return response.json()
}

/** Asks the agent to score the user's understanding (about half a minute). */
export async function requestAssessment(paperId: string): Promise<Assessment> {
  const response = await fetch(`/api/progress/${paperId}/assessment`, { method: 'POST' })
  if (!response.ok) throw new Error(`Scoring failed (${response.status}). Try again later.`)
  return response.json()
}

/** Records that the user confirmed a step, e.g. reading the paper. */
export async function confirmMilestone(paperId: string, item: MilestoneItem): Promise<void> {
  const response = await fetch(`/api/progress/${paperId}/milestone`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ item }),
  })
  if (!response.ok) throw new Error(`Request failed (${response.status}).`)
}
