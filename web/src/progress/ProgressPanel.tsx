import { ScoreCard } from './ScoreCard'
import type { Place, Progress } from './types'
import './progress.css'

type Props = {
  paperId: string
  progress: Progress | null
  onGo: (place: Place) => void
}

const PARTS: { key: Exclude<keyof Progress, 'completion' | 'confirmed'>; label: string }[] = [
  { key: 'reading', label: '1. Reading' },
  { key: 'summary', label: '2. Paper in 3 lines' },
  { key: 'podcast', label: '3. Podcast' },
  { key: 'video', label: '4. Explainer video' },
  { key: 'feed', label: '5. Learning feed' },
  { key: 'check', label: '6. Check your understanding' },
]

function percent(value: number): string {
  return `${Math.round(value * 100)}%`
}

/** Overall completion and each widget's share of it. */
export function ProgressPanel({ paperId, progress, onGo }: Props) {
  if (!progress) return <p className="analogy__status">Loading…</p>

  return (
    <div className="progress">
      <div className="progress__overall">
        <span className="progress__big">{percent(progress.completion)}</span>
        <span className="progress__caption">of this paper completed</span>
      </div>
      <ul className="progress__parts">
        {PARTS.map((part) => (
          <li key={part.key}>
            <span>{part.label}</span>
            <span className="progress__bar" aria-hidden>
              <span style={{ width: percent(progress[part.key]) }} />
            </span>
            <span className="progress__value">{percent(progress[part.key])}</span>
          </li>
        ))}
      </ul>
      <ScoreCard paperId={paperId} onGo={onGo} />
    </div>
  )
}
