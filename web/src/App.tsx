import { FeedPage } from './feed/FeedPage'
import { ReaderPage } from './reader/ReaderPage'

export default function App() {
  const feedPaperId = new URLSearchParams(window.location.search).get('feed')
  return feedPaperId ? <FeedPage paperId={feedPaperId} /> : <ReaderPage />
}
