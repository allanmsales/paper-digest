import type {
  Analogy,
  AskAnswer,
  CheckAttempt,
  CheckResult,
  Explanation,
  Lookup,
  Summary,
  ThreadMessage,
} from './types'

async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`/api/explainer/${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    const data = await response.json().catch(() => null)
    const detail =
      typeof data?.detail === 'string' ? data.detail : `Request failed (${response.status}).`
    throw new Error(detail)
  }

  return response.json()
}

export function explain(params: {
  selection: string
  page: number | null
  paperText: string
  guess: string | null
}): Promise<Explanation> {
  return post('explain', {
    selection: params.selection,
    page: params.page,
    paper_text: params.paperText,
    guess: params.guess,
  })
}

export function summarize(paperText: string): Promise<Summary> {
  return post('summary', { paper_text: paperText })
}

export function checkUnderstanding(
  paperText: string,
  section: number,
  answer: string,
): Promise<CheckResult> {
  return post('check', { paper_text: paperText, section, answer })
}

export function ask(
  paperText: string,
  anchor: string,
  messages: ThreadMessage[],
): Promise<AskAnswer> {
  return post('ask', {
    paper_text: paperText,
    anchor,
    messages: messages.map(({ role, content }) => ({ role, content })),
  })
}

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`/api/explainer/${path}`)
  if (!response.ok) throw new Error(`Request failed (${response.status}).`)
  return response.json()
}

/** This user's lookups on a paper, newest first. */
export function listLookups(paperId: string): Promise<Lookup[]> {
  return get(`${paperId}/lookups`)
}

/** This user's check answers on a paper, newest first. */
export function listChecks(paperId: string): Promise<CheckAttempt[]> {
  return get(`${paperId}/checks`)
}

export function analogy(paperText: string, subject: string): Promise<Analogy> {
  return post('analogy', { paper_text: paperText, subject })
}

/** Saves the paper and asks the API to prompt-cache it so the first
 *  lookup is fast. Resolves to the paper id, or null on failure. */
export async function warmPaper(paperText: string, source: string): Promise<string | null> {
  try {
    const { paper_id } = await post<{ paper_id: string }>('warm', {
      paper_text: paperText,
      source,
    })
    return paper_id
  } catch {
    // Best effort: lookups still work without a warm cache.
    return null
  }
}
