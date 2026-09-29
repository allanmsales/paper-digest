import type { Storyboard } from './types'
import { VisualView } from './Visuals'

/** Every scene at once, fully revealed, with its narration. */
export function StoryboardView({ board }: { board: Storyboard }) {
  return (
    <>
      {board.scenes.map((scene, index) => (
        <section key={index} className="scene">
          <header className="scene__header">
            <span className="scene__number">{index + 1}</span>
            <h2>{scene.title}</h2>
            <span className="scene__meta">
              {scene.visual.kind} · page {scene.page}
            </span>
          </header>
          <div className="scene__screen">
            <VisualView visual={scene.visual} />
          </div>
          <p className="scene__narration">🎙 {scene.narration}</p>
        </section>
      ))}
    </>
  )
}
