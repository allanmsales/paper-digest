from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    is_admin: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Session(SQLModel, table=True):
    """A signed-in browser; the token lives in an httpOnly cookie."""

    token: str = Field(primary_key=True)
    user_id: int = Field(index=True)
    expires_at: datetime
