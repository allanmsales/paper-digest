import type {
  Analogy,
  AskAnswer,
  CheckResult,
  Explanation,
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

export function analogy(paperText: string, subject: string): Promise<Analogy> {
  return post('analogy', { paper_text: paperText, subject })
}

/** Asks the API to prompt-cache the paper so the first lookup is fast. */
export function warmPaper(paperText: string): void {
  fetch('/api/explainer/warm', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ paper_text: paperText }),
  }).catch(() => {
    // Best effort: lookups still work without a warm cache.
  })
}
