import { useCallback, useEffect, useRef, useState } from 'react'

import { Fullscreen } from '../reader/Fullscreen'
import { fetchMap } from './api'
import { KnowledgeMap } from './KnowledgeMap'
import { STATE_LABEL } from './mapLayout'
import type { KnowledgeMapData, NodeState } from './types'
import './kmap.css'

const POLL_MS = 8000
const EVENT = 'pd:progress'

type Props = {
  paperId: string
}

/** The knowledge map in the side column; updates as the user learns. */
export function MapWidget({ paperId }: Props) {
  const [data, setData] = useState<KnowledgeMapData | null>(null)
  const [fullscreen, setFullscreen] = useState(false)
  const opener = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    let active = true
    const load = () =>
      fetchMap(paperId)
        .then((result) => active && setData(result))
        .catch(() => {})
    load()
    // Anything that counts as progress can change a concept's color.
    window.addEventListener(EVENT, load)
    return () => {
      active = false
      window.removeEventListener(EVENT, load)
    }
  }, [paperId])

  // The map appears once the feed's concepts (and their links) exist.
  useEffect(() => {
    if (data?.status !== 'building') return
    const timer = window.setTimeout(
      () =>
        fetchMap(paperId)
          .then(setData)
          .catch(() => {}),
      POLL_MS,
    )
    return () => window.clearTimeout(timer)
  }, [paperId, data])

  const closeFullscreen = useCallback(() => {
    setFullscreen(false)
    opener.current?.focus()
  }, [])

  if (!data) return <p className="analogy__status">Loading…</p>
  if (data.status === 'none')
    return <p className="analogy__status">The map appears once the learning feed is prepared.</p>
  if (data.status === 'building')
    return <p className="analogy__status">Drawing the map of concepts…</p>

  const counts = data.nodes.reduce(
    (all, node) => ({ ...all, [node.state]: (all[node.state] ?? 0) + 1 }),
    {} as Partial<Record<NodeState, number>>,
  )
  const needsWork = data.nodes.filter((node) => node.state === 'needs_work')

  return (
    <div className="kmap-widget">
      <div className="kmap-widget__bar">
        <span>
          {counts.solid ?? 0} of {data.nodes.length} concepts solid
        </span>
        <button
          ref={opener}
          className="video-widget__expand"
          onClick={() => setFullscreen(true)}
          aria-label="Open the map full screen"
          title="Full screen"
        >
          ⛶
        </button>
      </div>

      <button className="kmap-widget__thumb" onClick={() => setFullscreen(true)} tabIndex={-1}>
        <KnowledgeMap nodes={data.nodes} />
      </button>

      <ul className="kmap-legend">
        {(Object.keys(STATE_LABEL) as NodeState[]).map((state) => (
          <li key={state}>
            <span className={`kmap-legend__dot kmap__node--${state}`} />
            {STATE_LABEL[state]} {counts[state] ?? 0}
          </li>
        ))}
      </ul>

      {needsWork.length > 0 && (
        <p className="kmap-widget__focus">
          Needs work: {needsWork.map((node) => node.name).join(', ')}
        </p>
      )}

      <Fullscreen open={fullscreen} title="Knowledge map" onClose={closeFullscreen}>
        {fullscreen && (
          <div className="kmap-full">
            <p className="kmap-full__hint">
              Foundations at the top, the paper's own idea at the bottom. Hover a concept to
              see what it builds on.
            </p>
            <div className="kmap-full__canvas">
              <KnowledgeMap nodes={data.nodes} detailed />
            </div>
          </div>
        )}
      </Fullscreen>
    </div>
  )
}
