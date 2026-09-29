import { useEffect, useState } from 'react'

import { FeedPage } from './feed/FeedPage'
import { ReaderPage } from './reader/ReaderPage'
import { AdminPage } from './users/AdminPage'
import { me } from './users/api'
import { LoginPage } from './users/LoginPage'
import type { User } from './users/types'

export default function App() {
  // undefined while checking the session, null when signed out.
  const [user, setUser] = useState<User | null | undefined>(undefined)

  useEffect(() => {
    me()
      .then(setUser)
      .catch(() => setUser(null))
  }, [])

  if (user === undefined) return null
  if (user === null) return <LoginPage onLogin={setUser} />

  const params = new URLSearchParams(window.location.search)
  const feedPaperId = params.get('feed')
  if (feedPaperId) return <FeedPage paperId={feedPaperId} />
  if (params.has('admin') && user.is_admin) return <AdminPage user={user} />
  return <ReaderPage user={user} />
}
