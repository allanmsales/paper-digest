import { AnalogyButton } from './AnalogyButton'
import { AskThread } from './AskThread'
import { Text } from './Text'
import type { Explanation } from './types'

type Props = {
  result: Explanation
  /** The selected text, used as the analogy subject. */
  subject: string
  paperText: string | null
}

export function ExplanationCard({ result, subject, paperText }: Props) {
  return (
    <div className="explanation">
      {result.guess_feedback && (
        <p className="explanation__guess">
          <Text>{result.guess_feedback}</Text>
        </p>
      )}

      {result.meaning && (
        <p>
          <Text>{result.meaning}</Text>
        </p>
      )}

      {result.points.length > 0 && (
        <ul className="explanation__points">
          {result.points.map((point) => (
            <li key={point}>
              <Text>{point}</Text>
            </li>
          ))}
        </ul>
      )}

      {(result.defined_at || result.learn_first.length > 0) && (
        <p className="explanation__meta">
          {result.defined_at && <span>📍 {result.defined_at}</span>}
          {result.learn_first.length > 0 && <span>Learn first:</span>}
          {result.learn_first.map((item) => (
            <span key={item} className="explanation__chip">
              {item}
            </span>
          ))}
        </p>
      )}

      {paperText && (
        <div className="explanation__actions">
          <AnalogyButton paperText={paperText} subject={subject} />
          <AskThread
            paperText={paperText}
            anchor={`Selected text: "${subject}". Explanation shown: ${
              result.meaning ?? result.points.join(' ')
            }`}
          />
        </div>
      )}
    </div>
  )
}
