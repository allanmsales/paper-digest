from typing import Annotated

from fastapi import Cookie, Depends, HTTPException

from paper_digest.users.models import User
from paper_digest.users.store import session_user


SESSION_COOKIE = "pd_session"


def current_user(
    token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> User:
    user = session_user(token) if token else None
    if user is None:
        raise HTTPException(status_code=401, detail="Please sign in.")
    return user


def require_admin(user: Annotated[User, Depends(current_user)]) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admins only.")
    return user
