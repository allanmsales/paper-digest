import type { FlowVisual } from './types'

const NODE_W = 170
const NODE_H = 54
const GAP_X = 28
const GAP_Y = 44

/** Layered layout: a node sits one layer after its deepest parent. Long,
 *  narrow flows run left to right so they fit a 16:9 frame. */
function layout(visual: FlowVisual) {
  const depth = new Map<string, number>(visual.nodes.map((node) => [node.id, 0]))
  // Longest path by relaxation; capped so a cycle cannot loop forever.
  for (let round = 0; round < visual.nodes.length; round++) {
    let changed = false
    for (const edge of visual.edges) {
      const from = depth.get(edge.source)
      const to = depth.get(edge.target)
      if (from === undefined || to === undefined || to > from) continue
      depth.set(edge.target, from + 1)
      changed = true
    }
    if (!changed) break
  }

  const rows: string[][] = []
  for (const node of visual.nodes) {
    const row = depth.get(node.id) ?? 0
    ;(rows[row] ??= []).push(node.id)
  }
  const widest = Math.max(...rows.map((row) => row?.length ?? 0))
  const horizontal = rows.length > 3 && widest <= 2
  const position = new Map<string, { x: number; y: number }>()

  if (horizontal) {
    const height = widest * NODE_H + (widest - 1) * GAP_Y
    rows.forEach((row, layer) => {
      const rowHeight = row.length * NODE_H + (row.length - 1) * GAP_Y
      row.forEach((id, index) => {
        position.set(id, {
          x: layer * (NODE_W + GAP_X * 1.5),
          y: (height - rowHeight) / 2 + index * (NODE_H + GAP_Y),
        })
      })
    })
    return {
      position,
      horizontal,
      width: rows.length * (NODE_W + GAP_X * 1.5) - GAP_X * 1.5,
      height,
    }
  }

  const width = widest * NODE_W + (widest - 1) * GAP_X
  rows.forEach((row, layer) => {
    const rowWidth = row.length * NODE_W + (row.length - 1) * GAP_X
    row.forEach((id, index) => {
      position.set(id, {
        x: (width - rowWidth) / 2 + index * (NODE_W + GAP_X),
        y: layer * (NODE_H + GAP_Y),
      })
    })
  })
  return { position, horizontal, width, height: rows.length * (NODE_H + GAP_Y) - GAP_Y }
}

type Props = {
  visual: FlowVisual
  /** Nodes revealed so far, in narration order; Infinity shows everything. */
  beat?: number
}

export function FlowDiagram({ visual, beat = Infinity }: Props) {
  const { position, horizontal, width, height } = layout(visual)
  const order = visual.highlight_order.length
    ? visual.highlight_order
    : visual.nodes.map((node) => node.id)
  const step = new Map(order.map((id, index) => [id, index + 1]))
  const revealed = new Set(order.slice(0, beat))
  // Nodes outside the narration order show once the walk-through ends.
  const isShown = (id: string) =>
    revealed.has(id) || (!step.has(id) && beat >= order.length)
  const current = Number.isFinite(beat) ? order[beat - 1] : undefined

  return (
    <svg
      className="flow"
      viewBox={`-16 -16 ${width + 32} ${height + 32}`}
      style={{ maxWidth: width + 32 }}
      role="img"
    >
      <defs>
        <marker id="flow-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" className="flow__arrowhead" />
        </marker>
      </defs>
      {visual.edges.map((edge) => {
        const from = position.get(edge.source)
        const to = position.get(edge.target)
        if (!from || !to) return null
        // Arrows leave the bottom (or right) edge and enter the top (or left).
        const [x1, y1, x2, y2] = horizontal
          ? [from.x + NODE_W, from.y + NODE_H / 2, to.x - 2, to.y + NODE_H / 2]
          : [from.x + NODE_W / 2, from.y + NODE_H, to.x + NODE_W / 2, to.y - 2]
        return (
          <g
            key={`${edge.source}-${edge.target}`}
            className={`flow__edge-group${isShown(edge.source) && isShown(edge.target) ? '' : ' is-hidden'}`}
          >
            <line className="flow__edge" x1={x1} y1={y1} x2={x2} y2={y2} markerEnd="url(#flow-arrow)" />
            {edge.label && (
              <text
                className="flow__edge-label"
                x={(x1 + x2) / 2 + (horizontal ? 0 : 6)}
                y={(y1 + y2) / 2 + (horizontal ? -6 : 4)}
                textAnchor={horizontal ? 'middle' : 'start'}
              >
                {edge.label}
              </text>
            )}
          </g>
        )
      })}
      {visual.nodes.map((node) => {
        const at = position.get(node.id)!
        const number = step.get(node.id)
        const state = !isShown(node.id) ? ' is-hidden' : node.id === current ? ' is-current' : ''
        return (
          <g key={node.id} transform={`translate(${at.x}, ${at.y})`} className={`flow__group${state}`}>
            <rect className="flow__node" width={NODE_W} height={NODE_H} rx={8} />
            <foreignObject width={NODE_W} height={NODE_H}>
              <div className="flow__label">{node.label}</div>
            </foreignObject>
            {number && (
              <g transform={`translate(${NODE_W - 4}, -4)`}>
                <circle className="flow__badge" r={10} />
                <text className="flow__badge-text" textAnchor="middle" dy="4">
                  {number}
                </text>
              </g>
            )}
          </g>
        )
      })}
    </svg>
  )
}
