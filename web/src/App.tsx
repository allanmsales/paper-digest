import { useEffect, useState } from 'react'

import { AiBanner } from './ai/AiBanner'
import './ai/ai.css'
import { FeedPage } from './feed/FeedPage'
import { ReaderPage } from './reader/ReaderPage'
import { AdminPage } from './users/AdminPage'
import { me, setupStatus } from './users/api'
import { LoginPage } from './users/LoginPage'
import { SetupPage } from './users/SetupPage'
import type { User } from './users/types'

export default function App() {
  // undefined while checking the session, null when signed out.
  const [user, setUser] = useState<User | null | undefined>(undefined)
  const [needsSetup, setNeedsSetup] = useState(false)

  useEffect(() => {
    setupStatus()
      .then(async ({ needs_setup }) => {
        setNeedsSetup(needs_setup)
        setUser(needs_setup ? null : await me())
      })
      .catch(() => setUser(null))
  }, [])

  if (needsSetup) {
    return (
      <SetupPage
        onDone={(created) => {
          setNeedsSetup(false)
          setUser(created)
        }}
      />
    )
  }
  if (user === undefined) return null
  if (user === null) return <LoginPage onLogin={setUser} />

  const params = new URLSearchParams(window.location.search)
  const feedPaperId = params.get('feed')
  const isAdminPage = params.has('admin') && user.is_admin

  let page = <ReaderPage user={user} />
  if (feedPaperId) page = <FeedPage paperId={feedPaperId} />
  else if (isAdminPage) page = <AdminPage user={user} />

  return (
    <>
      {page}
      {!isAdminPage && <AiBanner isAdmin={user.is_admin} />}
    </>
  )
}
