import type { ReactNode } from 'react'

/** Renders *text* / **text** as emphasis; the model sometimes adds them. */
export function Text({ children }: { children: string }) {
  const parts: ReactNode[] = children
    .split(/\*{1,2}([^*]+)\*{1,2}/g)
    .map((part, index) => (index % 2 === 1 ? <em key={index}>{part}</em> : part))
  return <>{parts}</>
}
