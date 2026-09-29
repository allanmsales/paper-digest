import { useEffect, useLayoutEffect, useMemo, useRef, useState, type KeyboardEvent, type RefObject } from 'react'

import { beatAt, buildTimeline, sceneAt, sentenceAt } from './timeline'
import type { Narration, Storyboard } from './types'
import { VisualView } from './Visuals'

type Props = {
  board: Storyboard
  /** Narration audio and its timings; without them the video plays silently. */
  audioUrl?: string
  narration?: Narration | null
  /** Called with (time, total) while playing, to track what was watched. */
  onPlayed?: (time: number, total: number) => void
}

// The stage is laid out at this size and scaled to fit, like a video frame.
const STAGE_W = 960
const STAGE_H = 540

/** Scale that fits the fixed stage inside `frame`, tracking resizes. */
function useStageScale(frame: RefObject<HTMLDivElement | null>) {
  const [scale, setScale] = useState(1)
  useLayoutEffect(() => {
    const element = frame.current
    if (!element) return
    const update = () =>
      setScale(Math.min(element.clientWidth / STAGE_W, element.clientHeight / STAGE_H))
    update()
    const observer = new ResizeObserver(update)
    observer.observe(element)
    return () => observer.disconnect()
  }, [frame])
  return scale
}

function clock(seconds: number): string {
  const whole = Math.max(0, Math.floor(seconds))
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, '0')}`
}

/** A fake video: the visuals animate in step with the narration, shown as
 *  captions. With audio, the audio's clock drives everything. */
export function VideoPlayer({ board, audioUrl, narration, onPlayed }: Props) {
  const withAudio = !!audioUrl && !!narration
  const timeline = useMemo(
    () => buildTimeline(board, withAudio ? narration : null),
    [board, narration, withAudio],
  )
  const [time, setTime] = useState(0)
  const [playing, setPlaying] = useState(false)
  const last = useRef<number | null>(null)
  const audio = useRef<HTMLAudioElement>(null)
  const frame = useRef<HTMLDivElement>(null)
  const scale = useStageScale(frame)

  useEffect(() => {
    if (!playing) return
    let frame = 0
    const tick = (now: number) => {
      const delta = last.current === null ? 0 : (now - last.current) / 1000
      last.current = now
      if (audio.current) {
        setTime(audio.current.currentTime)
        frame = requestAnimationFrame(tick)
        return
      }
      setTime((current) => {
        const next = current + delta
        if (next >= timeline.total) {
          setPlaying(false)
          return timeline.total
        }
        return next
      })
      frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => {
      cancelAnimationFrame(frame)
      last.current = null
    }
  }, [playing, timeline.total])

  useEffect(() => {
    if (playing) onPlayed?.(time, timeline.total)
  }, [playing, time, timeline.total, onPlayed])

  const scene = sceneAt(timeline, time)
  const offset = time - scene.start
  const sentence = sentenceAt(scene, offset)
  const beat = beatAt(scene, sentence)
  const current = board.scenes[scene.index]
  const ended = time >= timeline.total

  function seek(seconds: number) {
    const target = Math.min(Math.max(seconds, 0), timeline.total)
    if (audio.current) audio.current.currentTime = target
    setTime(target)
  }

  function goToScene(index: number) {
    const target = timeline.scenes[Math.min(Math.max(index, 0), timeline.scenes.length - 1)]
    seek(target.start)
  }

  function togglePlay() {
    const player = audio.current
    if (player) {
      if (player.paused) {
        if (ended) seek(0)
        // Autoplay rules may refuse; then we just stay paused.
        player.play().catch(() => setPlaying(false))
      } else {
        player.pause()
      }
      return
    }
    if (ended) setTime(0)
    setPlaying(!playing || ended)
  }

  // Shortcuts only while the player has focus, so the page keeps its keys.
  function onKey(event: KeyboardEvent<HTMLDivElement>) {
    if (event.target instanceof HTMLInputElement && event.target.type !== 'range') return
    if (event.key === ' ') {
      event.preventDefault()
      togglePlay()
    } else if (event.key === 'ArrowRight') {
      event.preventDefault()
      goToScene(scene.index + 1)
    } else if (event.key === 'ArrowLeft') {
      event.preventDefault()
      goToScene(offset > 2 ? scene.index : scene.index - 1)
    }
  }

  return (
    <div className="player" tabIndex={0} onKeyDown={onKey} aria-label="Explainer video">
      {withAudio && (
        <audio
          ref={audio}
          src={audioUrl}
          preload="auto"
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
          onEnded={() => {
            setPlaying(false)
            setTime(timeline.total)
          }}
        />
      )}
      <div className="player__frame" ref={frame}>
      <div
        className="player__stage"
        onClick={togglePlay}
        style={{
          transform: `scale(${scale})`,
          left: `calc(50% - ${(STAGE_W * scale) / 2}px)`,
        }}
      >
        <div className="player__chip">
          {scene.index + 1}. {current.title}
        </div>
        <div className="player__visual" key={scene.index}>
          <VisualView visual={current.visual} beat={beat} />
        </div>
        <p className="player__caption" key={`${scene.index}-${sentence}`}>
          {scene.sentences[sentence]?.text}
        </p>
        {!playing && (
          <div className="player__overlay" aria-hidden>
            <span>{ended ? '↻' : '▶'}</span>
          </div>
        )}
      </div>
      </div>

      <div className="player__controls">
        <button onClick={togglePlay} aria-label={playing ? 'Pause' : 'Play'}>
          {playing ? '❚❚' : ended ? '↻' : '▶'}
        </button>
        <button onClick={() => goToScene(scene.index - 1)} aria-label="Previous scene">
          ⏮
        </button>
        <button onClick={() => goToScene(scene.index + 1)} aria-label="Next scene">
          ⏭
        </button>
        <div className="player__scrubber">
          <input
            type="range"
            min={0}
            max={timeline.total}
            step={0.1}
            value={time}
            onChange={(event) => seek(Number(event.target.value))}
            aria-label="Seek"
          />
          <div className="player__marks" aria-hidden>
            {timeline.scenes.slice(1).map((item) => (
              <span key={item.index} style={{ left: `${(item.start / timeline.total) * 100}%` }} />
            ))}
          </div>
        </div>
        <span className="player__time">
          {clock(time)} / {clock(timeline.total)}
        </span>
      </div>

    </div>
  )
}
