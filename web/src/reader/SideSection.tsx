import type { ReactNode } from 'react'

type Props = {
  title: string
  count?: number
  open: boolean
  onToggle: () => void
  children: ReactNode
}

/** One folding section of the reader's right column. */
export function SideSection({ title, count, open, onToggle, children }: Props) {
  return (
    <section className={`side-section${open ? ' is-open' : ''}`}>
      <button className="side-section__header" onClick={onToggle} aria-expanded={open}>
        <span>
          {title}
          {count !== undefined && count > 0 && (
            <span className="side-section__count">{count}</span>
          )}
        </span>
        <span className="side-section__chevron" aria-hidden>
          ›
        </span>
      </button>
      {open && <div className="side-section__body">{children}</div>}
    </section>
  )
}
