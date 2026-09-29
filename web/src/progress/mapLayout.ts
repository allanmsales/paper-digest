import type { MapNode, NodeState } from './types'

export const STATE_LABEL: Record<NodeState, string> = {
  not_started: 'Not started',
  learning: 'Learning',
  solid: 'Solid',
  needs_work: 'Needs work',
}

export const NODE_W = 112
export const NODE_H = 44
const GAP_X = 14
const GAP_Y = 46

export type Placed = { node: MapNode; x: number; y: number; layer: number }

/** Top-down layers: foundations first, each concept one layer below its
 *  deepest prerequisite. Nodes in a layer are ordered by the average
 *  position of their prerequisites, which keeps most edges short. */
export function layoutMap(nodes: MapNode[]) {
  const byName = new Map(nodes.map((node) => [node.name, node]))
  const depth = new Map<string, number>()
  const depthOf = (name: string): number => {
    const known = depth.get(name)
    if (known !== undefined) return known
    depth.set(name, 0) // guards against a cycle slipping through
    const node = byName.get(name)
    const value = node
      ? 1 + Math.max(-1, ...node.requires.filter((need) => byName.has(need)).map(depthOf))
      : 0
    depth.set(name, value)
    return value
  }
  nodes.forEach((node) => depthOf(node.name))

  const layers: MapNode[][] = []
  for (const node of nodes) (layers[depth.get(node.name)!] ??= []).push(node)

  const order = new Map<string, number>()
  layers.forEach((layer, index) => {
    if (index > 0) {
      const center = (node: MapNode) => {
        const parents = node.requires.map((need) => order.get(need)).filter((x) => x !== undefined)
        return parents.length ? parents.reduce((a, b) => a + b, 0) / parents.length : Infinity
      }
      layer.sort((a, b) => center(a) - center(b))
    }
    layer.forEach((node, position) => order.set(node.name, position - (layer.length - 1) / 2))
  })

  const widest = Math.max(...layers.map((layer) => layer.length))
  const width = widest * NODE_W + (widest - 1) * GAP_X
  const placed = new Map<string, Placed>()
  layers.forEach((layer, index) => {
    const rowWidth = layer.length * NODE_W + (layer.length - 1) * GAP_X
    layer.forEach((node, position) => {
      placed.set(node.name, {
        node,
        layer: index,
        x: (width - rowWidth) / 2 + position * (NODE_W + GAP_X),
        y: index * (NODE_H + GAP_Y),
      })
    })
  })
  return { placed, width, height: layers.length * (NODE_H + GAP_Y) - GAP_Y }
}

/** A concept and everything it builds on, directly or not. */
export function ancestors(name: string, nodes: MapNode[]): Set<string> {
  const byName = new Map(nodes.map((node) => [node.name, node]))
  const seen = new Set<string>()
  const visit = (current: string) => {
    if (seen.has(current)) return
    seen.add(current)
    byName.get(current)?.requires.forEach(visit)
  }
  visit(name)
  return seen
}
