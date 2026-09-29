import { useEffect, type ReactNode } from 'react'

type Props = {
  open: boolean
  title: string
  onClose: () => void
  children: ReactNode
}

/** Shows its children over the whole window while `open`. The children stay
 *  mounted either way, so a playing video keeps playing. Esc or × closes. */
export function Fullscreen({ open, title, onClose, children }: Props) {
  useEffect(() => {
    if (!open) return
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    const overflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    // Lifts the side column's stacking context above the sticky page header.
    document.body.classList.add('has-fullscreen')
    window.addEventListener('keydown', onKey)
    return () => {
      document.body.style.overflow = overflow
      document.body.classList.remove('has-fullscreen')
      window.removeEventListener('keydown', onKey)
    }
  }, [open, onClose])

  return (
    <div
      className={`fullscreen${open ? ' is-open' : ''}`}
      role={open ? 'dialog' : undefined}
      aria-modal={open || undefined}
      aria-label={open ? title : undefined}
    >
      {open && (
        <header className="fullscreen__header">
          <h2>{title}</h2>
          <button className="fullscreen__close" onClick={onClose} aria-label="Close full screen">
            ×
          </button>
        </header>
      )}
      <div className="fullscreen__body">{children}</div>
    </div>
  )
}
