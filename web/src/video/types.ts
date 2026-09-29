export type FlowVisual = {
  kind: 'flow'
  nodes: { id: string; label: string }[]
  edges: { source: string; target: string; label: string | null }[]
  highlight_order: string[]
}

export type EquationVisual = {
  kind: 'equation'
  latex: string
  terms: { latex: string; meaning: string }[]
}

export type ExampleVisual = {
  kind: 'example'
  inputs: { name: string; value: number; meaning: string }[]
  steps: {
    name: string
    label: string
    expression: string
    value: number | null
    error: string | null
  }[]
  takeaway: string
}

export type ChartVisual = {
  kind: 'chart'
  title: string
  unit: string
  bars: { label: string; value: number }[]
}

export type Visual = FlowVisual | EquationVisual | ExampleVisual | ChartVisual

export type Scene = {
  title: string
  narration: string
  page: number
  visual: Visual
}

export type Storyboard = {
  title: string
  scenes: Scene[]
  check_question: string
}

export type Narration = {
  total: number
  scenes: {
    start: number
    end: number
    sentences: { text: string; start: number; end: number }[]
  }[]
}

export type NarrationState = {
  status: 'none' | 'running' | 'ready' | 'failed'
  detail: string | null
  narration: Narration | null
}
