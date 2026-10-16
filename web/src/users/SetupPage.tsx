import { useState, type FormEvent } from 'react'

import { AiSettingsForm } from '../ai/AiSettingsForm'
import { setup } from './api'
import type { User } from './types'
import './users.css'

type Props = {
  onDone: (user: User) => void
}

/** First run: create the admin account, then pick an AI provider. */
export function SetupPage({ onDone }: Props) {
  const [step, setStep] = useState<'account' | 'ai' | 'done'>('account')
  const [user, setUser] = useState<User | null>(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function handleAccount(event: FormEvent) {
    event.preventDefault()
    if (password !== confirm) {
      setError('The passwords do not match.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      setUser(await setup(email, password))
      setStep('ai')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Setup failed.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="setup">
      <div className="setup__card">
        <h1>Welcome to Paper Digest</h1>
        <ol className="setup__steps">
          <li className={step === 'account' ? 'is-current' : 'is-done'}>Your account</li>
          <li className={step === 'ai' ? 'is-current' : step === 'done' ? 'is-done' : ''}>
            AI provider
          </li>
          <li className={step === 'done' ? 'is-current' : ''}>Start reading</li>
        </ol>

        {step === 'account' && (
          <form className="setup__form" onSubmit={handleAccount}>
            <p>
              Create the admin account for this computer. You can add more people later in
              Admin.
            </p>
            <label>
              Email
              <input
                type="email"
                autoComplete="username"
                required
                autoFocus
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>
            <label>
              Password <span>(min 6 characters)</span>
              <input
                type="password"
                autoComplete="new-password"
                minLength={6}
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>
            <label>
              Repeat password
              <input
                type="password"
                autoComplete="new-password"
                minLength={6}
                required
                value={confirm}
                onChange={(event) => setConfirm(event.target.value)}
              />
            </label>
            {error && <p className="users__error">{error}</p>}
            <button className="users__primary" type="submit" disabled={busy}>
              {busy ? 'Creating…' : 'Create account'}
            </button>
          </form>
        )}

        {step === 'ai' && (
          <>
            <p>
              Paper Digest uses an AI model to explain, summarize and quiz. Pick a provider,
              paste your key, and click <strong>Test connection</strong> before saving.
            </p>
            <AiSettingsForm onSaved={() => setStep('done')} />
            <button className="setup__skip" onClick={() => setStep('done')}>
              Skip for now (set it later in Admin)
            </button>
          </>
        )}

        {step === 'done' && user && (
          <div className="setup__form">
            <p>You’re all set. Open a paper by URL or upload a PDF to start reading.</p>
            <button className="users__primary" onClick={() => onDone(user)}>
              Start reading
            </button>
          </div>
        )}
      </div>
    </main>
  )
}
