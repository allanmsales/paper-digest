import katex from 'katex'
import 'katex/dist/katex.min.css'

type Props = {
  latex: string
  display?: boolean
}

export function Tex({ latex, display = false }: Props) {
  const html = katex.renderToString(latex, { displayMode: display, throwOnError: false })
  return <span className="tex" dangerouslySetInnerHTML={{ __html: html }} />
}
