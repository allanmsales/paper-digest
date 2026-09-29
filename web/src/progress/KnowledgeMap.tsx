import { useMemo, useState } from 'react'

import { ancestors, layoutMap, NODE_H, NODE_W, STATE_LABEL } from './mapLayout'
import type { MapNode } from './types'

type Props = {
  nodes: MapNode[]
  /** Draw names readable (full screen) or as a compact overview. */
  detailed?: boolean
}

/** The paper's concepts as a top-down hierarchy, colored by progress. */
export function KnowledgeMap({ nodes, detailed = false }: Props) {
  const { placed, width, height } = useMemo(() => layoutMap(nodes), [nodes])
  const [focus, setFocus] = useState<string | null>(null)
  const lit = useMemo(() => (focus ? ancestors(focus, nodes) : null), [focus, nodes])
  const pad = 12

  return (
    <svg
      className={`kmap${detailed ? ' kmap--detailed' : ''}`}
      viewBox={`${-pad} ${-pad} ${width + pad * 2} ${height + pad * 2}`}
      style={detailed ? { width: width + pad * 2, minWidth: '100%' } : undefined}
      role="img"
      aria-label="Knowledge map of the paper's concepts"
    >
      {[...placed.values()].flatMap(({ node, x, y }) =>
        node.requires.map((need) => {
          const from = placed.get(need)
          if (!from) return null
          const x1 = from.x + NODE_W / 2
          const y1 = from.y + NODE_H
          const x2 = x + NODE_W / 2
          const y2 = y
          const bend = (y2 - y1) / 2
          const on = !lit || (lit.has(node.name) && lit.has(need))
          return (
            <path
              key={`${need}->${node.name}`}
              className={`kmap__edge${on ? '' : ' is-dim'}${lit && on ? ' is-lit' : ''}`}
              d={`M${x1},${y1} C${x1},${y1 + bend} ${x2},${y2 - bend} ${x2},${y2}`}
            />
          )
        }),
      )}
      {[...placed.values()].map(({ node, x, y }) => (
        <g
          key={node.name}
          transform={`translate(${x}, ${y})`}
          className={`kmap__node kmap__node--${node.state}${node.is_main ? ' is-main' : ''}${
            lit && !lit.has(node.name) ? ' is-dim' : ''
          }`}
          onMouseEnter={() => setFocus(node.name)}
          onMouseLeave={() => setFocus(null)}
        >
          <title>
            {node.name} · {STATE_LABEL[node.state]}
            {node.posts ? ` · ${node.seen}/${node.posts} posts` : ''}
          </title>
          <rect width={NODE_W} height={NODE_H} rx={8} />
          <foreignObject width={NODE_W} height={NODE_H}>
            <div className="kmap__label">{node.name}</div>
          </foreignObject>
        </g>
      ))}
    </svg>
  )
}
