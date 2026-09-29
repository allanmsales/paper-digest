export type Explanation = {
  /** Set for a term. */
  meaning: string | null
  /** Set for a longer passage. */
  points: string[]
  defined_at: string | null
  learn_first: string[]
  guess_feedback: string | null
}

export type SelectedText = {
  text: string
  /** Page the selection is on. */
  page: number | null
  rect: { top: number; left: number; bottom: number }
}

export type Lookup = {
  id: number
  selection: string
  guess: string | null
  result: Explanation
}

export type PaperSection = {
  title: string
  page: number
  key_ideas: string[]
}

export type Summary = {
  problem: string
  idea: string
  result: string
  sections: PaperSection[]
}

export type Analogy = {
  analogy: string
  mapping: { everyday: string; term: string }[]
}

export type CheckResult = {
  level: 'got_it' | 'partly' | 'not_yet'
  ideas: { idea: string; covered: boolean; reread_at: string | null }[]
}

/** A saved check answer, newest first from the API. */
export type CheckAttempt = {
  section: number
  answer: string
  result: CheckResult
}

export type ThreadMessage = {
  role: 'reader' | 'assistant'
  content: string
  reread_at?: string | null
}

export type AskAnswer = {
  answer: string
  reread_at: string | null
}
