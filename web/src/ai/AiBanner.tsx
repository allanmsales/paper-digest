import { useEffect, useState } from 'react'

import { aiStatus } from './api'

/** Shown when no AI provider is set: AI features would fail until then. */
export function AiBanner({ isAdmin }: { isAdmin: boolean }) {
  const [configured, setConfigured] = useState(true)

  useEffect(() => {
    aiStatus()
      .then((status) => setConfigured(status.configured))
      .catch(() => {
        // Keep quiet if the status can't be read.
      })
  }, [])

  if (configured) return null

  return (
    <div className="ai-banner" role="status">
      AI features are off: no AI provider is set up.{' '}
      {isAdmin ? <a href="/?admin">Set one up in Admin →</a> : 'Ask your admin to set one up.'}
    </div>
  )
}
