import { useEffect, useState, type FormEvent } from 'react'

import { changePassword, createUser, deleteUser, listUsers } from './api'
import type { User } from './types'
import { UserMenu } from './UserMenu'
import './users.css'

type Props = {
  user: User
}

/** Add and remove users, and reset their passwords. Admins only. */
export function AdminPage({ user }: Props) {
  const [users, setUsers] = useState<User[]>([])
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isAdmin, setIsAdmin] = useState(false)
  const [resetting, setResetting] = useState<number | null>(null)
  const [newPassword, setNewPassword] = useState('')

  function refresh() {
    listUsers()
      .then(setUsers)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed.'))
  }

  useEffect(refresh, [])

  async function run(action: () => Promise<unknown>, done: string) {
    setError(null)
    setNotice(null)
    try {
      await action()
      setNotice(done)
      refresh()
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed.')
      return false
    }
  }

  async function handleCreate(event: FormEvent) {
    event.preventDefault()
    if (await run(() => createUser(email, password, isAdmin), `Added ${email}.`)) {
      setEmail('')
      setPassword('')
      setIsAdmin(false)
    }
  }

  async function handleReset(event: FormEvent, target: User) {
    event.preventDefault()
    if (await run(() => changePassword(target.id, newPassword), `Password changed for ${target.email}.`)) {
      setResetting(null)
      setNewPassword('')
    }
  }

  function handleDelete(target: User) {
    if (!window.confirm(`Delete ${target.email}? This cannot be undone.`)) return
    run(() => deleteUser(target.id), `Deleted ${target.email}.`)
  }

  return (
    <div className="admin">
      <header className="admin__header">
        <a className="admin__back" href="/">
          ← Reader
        </a>
        <h1>Users</h1>
        <UserMenu user={user} />
      </header>

      <main className="admin__main">
        {error && <p className="users__error">{error}</p>}
        {notice && <p className="users__notice">{notice}</p>}

        <table className="admin__table">
          <thead>
            <tr>
              <th>Email</th>
              <th>Role</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {users.map((target) => (
              <tr key={target.id}>
                <td>{target.email}</td>
                <td>{target.is_admin ? 'Admin' : 'Reader'}</td>
                <td className="admin__actions">
                  {resetting === target.id ? (
                    <form onSubmit={(event) => handleReset(event, target)}>
                      <input
                        type="password"
                        placeholder="New password"
                        autoComplete="new-password"
                        minLength={6}
                        required
                        autoFocus
                        value={newPassword}
                        onChange={(event) => setNewPassword(event.target.value)}
                      />
                      <button type="submit">Save</button>
                      <button type="button" onClick={() => setResetting(null)}>
                        Cancel
                      </button>
                    </form>
                  ) : (
                    <>
                      <button
                        onClick={() => {
                          setResetting(target.id)
                          setNewPassword('')
                        }}
                      >
                        Change password
                      </button>
                      {target.id !== user.id && (
                        <button className="admin__danger" onClick={() => handleDelete(target)}>
                          Delete
                        </button>
                      )}
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <form className="admin__add" onSubmit={handleCreate}>
          <h2>Add user</h2>
          <input
            type="email"
            placeholder="Email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <input
            type="password"
            placeholder="Password (min 6)"
            autoComplete="new-password"
            minLength={6}
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          <label className="admin__check">
            <input
              type="checkbox"
              checked={isAdmin}
              onChange={(event) => setIsAdmin(event.target.checked)}
            />
            Admin
          </label>
          <button className="users__primary" type="submit">
            Add
          </button>
        </form>
      </main>
    </div>
  )
}
