export type AudioStatus = 'none' | 'running' | 'ready' | 'failed'

export type ScriptLine = {
  speaker: 'host' | 'author'
  text: string
}

export type Script = {
  title: string
  lines: ScriptLine[]
}
