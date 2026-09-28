import { useState, type FormEvent } from 'react'

import { ask } from './api'
import { Text } from './Text'
import type { ThreadMessage } from './types'

type Props = {
  paperText: string
  /** What the questions are about, sent with every question. */
  anchor: string
}

/** A small question thread tied to one point of the paper. */
export function AskThread({ paperText, anchor }: Props) {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<ThreadMessage[]>([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const text = question.trim()
    if (!text) return
    const thread: ThreadMessage[] = [...messages, { role: 'reader', content: text }]
    setMessages(thread)
    setQuestion('')
    setLoading(true)
    setError(null)
    try {
      const reply = await ask(paperText, anchor, thread)
      setMessages([
        ...thread,
        { role: 'assistant', content: reply.answer, reread_at: reply.reread_at },
      ])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  if (!open) {
    return (
      <button className="analogy__trigger" onClick={() => setOpen(true)}>
        💬 Ask
      </button>
    )
  }

  return (
    <div className="ask">
      {messages.map((message, index) => (
        <div key={index} className={`ask__message ask__message--${message.role}`}>
          <Text>{message.content}</Text>
          {message.reread_at && <span className="check__reread">Reread: {message.reread_at}</span>}
        </div>
      ))}
      {loading && <p className="analogy__status">Thinking…</p>}
      {error && <p className="analogy__error">{error}</p>}
      <form className="ask__form" onSubmit={handleSubmit}>
        <input
          autoFocus
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="What is unclear?"
          aria-label="Your question"
        />
        <button type="submit" disabled={loading || !question.trim()}>
          Ask
        </button>
      </form>
    </div>
  )
}
