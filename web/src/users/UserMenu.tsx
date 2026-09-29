import { logout } from './api'
import type { User } from './types'

type Props = {
  user: User
}

export function UserMenu({ user }: Props) {
  async function handleLogout() {
    await logout().catch(() => {})
    window.location.href = '/'
  }

  return (
    <nav className="user-menu">
      <span className="user-menu__email">{user.email}</span>
      {user.is_admin && <a href="/?admin">Admin</a>}
      <button onClick={handleLogout}>Log out</button>
    </nav>
  )
}
