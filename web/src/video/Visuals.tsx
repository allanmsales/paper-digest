import { useEffect, useRef, useState } from 'react'

import { FlowDiagram } from './FlowDiagram'
import { formatNumber } from './format'
import { Tex } from './Tex'
import type { ChartVisual, EquationVisual, ExampleVisual, Visual } from './types'

type BeatProps = {
  /** Reveal steps shown so far; Infinity shows everything (storyboard). */
  beat?: number
}

const COUNT_MS = 700

/** Counts up to `value` the first time it appears, like a calculation running. */
function CountUp({ value }: { value: number }) {
  const [shown, setShown] = useState(0)
  const frame = useRef(0)

  useEffect(() => {
    const started = performance.now()
    const tick = (now: number) => {
      const progress = Math.min(1, (now - started) / COUNT_MS)
      setShown(value * (1 - (1 - progress) ** 3))
      if (progress < 1) frame.current = requestAnimationFrame(tick)
    }
    frame.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame.current)
  }, [value])

  return <>{formatNumber(shown)}</>
}

function stateOf(index: number, beat: number): string {
  if (index >= beat) return ' is-hidden'
  return Number.isFinite(beat) && index === beat - 1 ? ' is-current' : ''
}

function EquationView({ visual, beat = Infinity }: { visual: EquationVisual } & BeatProps) {
  return (
    <div className="equation">
      <div className="equation__main">
        <Tex latex={visual.latex} display />
      </div>
      <dl className="equation__terms">
        {visual.terms.map((term, index) => (
          <div key={term.latex} className={`reveal${stateOf(index, beat)}`}>
            <dt>
              <Tex latex={term.latex} />
            </dt>
            <dd>{term.meaning}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

function ExampleView({ visual, beat = Infinity }: { visual: ExampleVisual } & BeatProps) {
  const animate = Number.isFinite(beat)
  return (
    <div className="example">
      <table>
        <tbody>
          {visual.inputs.map((input) => (
            <tr key={input.name} className={`example__input reveal${beat >= 1 ? '' : ' is-hidden'}`}>
              <td className="example__name">{input.name}</td>
              <td className="example__value">{formatNumber(input.value)}</td>
              <td className="example__meaning">{input.meaning}</td>
            </tr>
          ))}
          {visual.steps.map((step, index) => (
            <tr key={step.name} className={`example__step reveal${stateOf(index + 1, beat)}`}>
              <td className="example__name">{step.name}</td>
              <td className="example__value">
                {step.value === null
                  ? '—'
                  : animate && index + 1 < beat
                    ? <CountUp value={step.value} />
                    : formatNumber(step.value)}
              </td>
              <td className="example__meaning">
                {step.label}
                <code>= {step.expression}</code>
                {step.error && <span className="example__error">{step.error}</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className={`example__takeaway reveal${beat > visual.steps.length ? '' : ' is-hidden'}`}>
        {visual.takeaway}
      </p>
    </div>
  )
}

function ChartView({ visual, beat = Infinity }: { visual: ChartVisual } & BeatProps) {
  const max = Math.max(...visual.bars.map((bar) => Math.abs(bar.value)), 1e-9)
  return (
    <figure className="chart">
      <figcaption>
        {visual.title} <span>({visual.unit})</span>
      </figcaption>
      {visual.bars.map((bar, index) => (
        <div key={bar.label} className={`chart__row${index < beat ? '' : ' is-empty'}`}>
          <span className="chart__label">{bar.label}</span>
          <div className="chart__track">
            <div
              className="chart__bar"
              style={{ width: index < beat ? `${(Math.abs(bar.value) / max) * 100}%` : 0 }}
            />
          </div>
          <span className="chart__value">{formatNumber(bar.value)}</span>
        </div>
      ))}
    </figure>
  )
}

export function VisualView({ visual, beat }: { visual: Visual } & BeatProps) {
  switch (visual.kind) {
    case 'flow':
      return <FlowDiagram visual={visual} beat={beat} />
    case 'equation':
      return <EquationView visual={visual} beat={beat} />
    case 'example':
      return <ExampleView visual={visual} beat={beat} />
    case 'chart':
      return <ChartView visual={visual} beat={beat} />
  }
}
