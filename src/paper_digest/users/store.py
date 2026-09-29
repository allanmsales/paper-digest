import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlmodel import delete, func, select

from paper_digest.core.db import db_session
from paper_digest.users.models import Session, User
from paper_digest.users.passwords import hash_password, verify_password


SESSION_DAYS = 30


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user(user_id: int) -> User | None:
    with db_session() as session:
        return session.get(User, user_id)


def find_user(email: str) -> User | None:
    with db_session() as session:
        return session.exec(select(User).where(User.email == normalize_email(email))).first()


def list_users() -> list[User]:
    with db_session() as session:
        return list(session.exec(select(User).order_by(User.email)))


def create_user(email: str, password: str, is_admin: bool = False) -> User:
    if find_user(email) is not None:
        raise ValueError("A user with this email already exists.")
    user = User(email=normalize_email(email), password_hash=hash_password(password), is_admin=is_admin)
    with db_session() as session:
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


def set_password(user_id: int, password: str) -> None:
    with db_session() as session:
        user = session.get(User, user_id)
        if user is None:
            raise LookupError("User not found.")
        user.password_hash = hash_password(password)
        session.add(user)
        # A new password signs the user out everywhere.
        session.exec(delete(Session).where(Session.user_id == user_id))
        session.commit()


def delete_user(user_id: int) -> None:
    with db_session() as session:
        user = session.get(User, user_id)
        if user is None:
            raise LookupError("User not found.")
        session.exec(delete(Session).where(Session.user_id == user_id))
        session.delete(user)
        session.commit()


def count_admins() -> int:
    with db_session() as session:
        return session.exec(select(func.count()).select_from(User).where(User.is_admin)).one()


def authenticate(email: str, password: str) -> User | None:
    user = find_user(email)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def open_session(user_id: int) -> tuple[str, datetime]:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(days=SESSION_DAYS)
    with db_session() as session:
        session.add(Session(token=token, user_id=user_id, expires_at=expires_at))
        session.commit()
    return token, expires_at


def session_user(token: str) -> User | None:
    with db_session() as session:
        row = session.get(Session, token)
        if row is None:
            return None
        # SQLite drops the timezone.
        if row.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
            session.delete(row)
            session.commit()
            return None
        return session.get(User, row.user_id)


def close_session(token: str) -> None:
    with db_session() as session:
        row = session.get(Session, token)
        if row is not None:
            session.delete(row)
            session.commit()


def claim_unowned_rows(tables: list[str]) -> None:
    """Gives rows saved before accounts existed to the first admin."""
    with db_session() as session:
        admin = session.exec(select(User).where(User.is_admin).order_by(User.id)).first()
        if admin is None:
            return
        for table in tables:
            session.execute(
                text(f'UPDATE "{table}" SET user_id = :user_id WHERE user_id IS NULL'),
                {"user_id": admin.id},
            )
        session.commit()
