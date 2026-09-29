import type { Narration, Storyboard, Visual } from './types'

export type TimedSentence = { text: string; start: number; end: number }

export type TimedScene = {
  index: number
  start: number
  duration: number
  sentences: TimedSentence[]
  beats: number
}

export type Timeline = { scenes: TimedScene[]; total: number }

const SECONDS_PER_WORD = 0.38
const SENTENCE_PAUSE = 0.35
const MIN_SENTENCE = 1.4

/** A sentence ends at . ! or ? (optionally closed by a quote or bracket)
 *  followed by whitespace, so decimals like 0.58 stay whole. Same rule as
 *  the API's split_sentences. */
export function splitSentences(text: string): string[] {
  const parts = text.trim().split(/(?<=[.!?]["')\]]?)\s+/)
  return parts.map((part) => part.trim()).filter(Boolean)
}

/** How many reveal steps a visual has; the narration advances through them. */
export function beatCount(visual: Visual): number {
  switch (visual.kind) {
    case 'flow':
      return (visual.highlight_order.length || visual.nodes.length) || 1
    case 'equation':
      return visual.terms.length || 1
    case 'example':
      // Inputs first, then one beat per computed step.
      return 1 + visual.steps.length
    case 'chart':
      return visual.bars.length || 1
  }
}

/** Uses the narration audio's real sentence timings when there are any;
 *  otherwise estimates them from word counts (silent, captions only). */
export function buildTimeline(board: Storyboard, narration?: Narration | null): Timeline {
  if (narration && narration.scenes.length === board.scenes.length) {
    return {
      total: narration.total,
      scenes: narration.scenes.map((scene, index) => ({
        index,
        start: scene.start,
        duration: scene.end - scene.start,
        sentences: scene.sentences.map((sentence) => ({
          text: sentence.text,
          start: sentence.start - scene.start,
          end: sentence.end - scene.start,
        })),
        beats: beatCount(board.scenes[index].visual),
      })),
    }
  }

  let clock = 0
  const scenes = board.scenes.map((scene, index) => {
    let t = 0
    const sentences = splitSentences(scene.narration).map((text) => {
      const words = text.split(/\s+/).length
      const length = Math.max(MIN_SENTENCE, words * SECONDS_PER_WORD) + SENTENCE_PAUSE
      const sentence = { text, start: t, end: t + length }
      t += length
      return sentence
    })
    const timed = { index, start: clock, duration: t, sentences, beats: beatCount(scene.visual) }
    clock += t
    return timed
  })
  return { scenes, total: clock }
}

export function sceneAt(timeline: Timeline, time: number): TimedScene {
  return (
    timeline.scenes.find((scene) => time < scene.start + scene.duration) ??
    timeline.scenes[timeline.scenes.length - 1]
  )
}

/** Index of the sentence being spoken `offset` seconds into the scene. */
export function sentenceAt(scene: TimedScene, offset: number): number {
  const index = scene.sentences.findIndex((sentence) => offset < sentence.end)
  return index === -1 ? scene.sentences.length - 1 : index
}

/** Beats revealed while sentence `sentence` is spoken: spread evenly, all
 *  revealed by the last sentence. */
export function beatAt(scene: TimedScene, sentence: number): number {
  const total = scene.sentences.length || 1
  return Math.min(scene.beats, Math.ceil(((sentence + 1) * scene.beats) / total))
}
