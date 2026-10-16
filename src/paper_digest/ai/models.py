from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class AiSettings(SQLModel, table=True):
    """The app-wide AI provider (a single row, id 1). Stored in the local
    database; the key is never sent back to the browser."""

    id: int = Field(default=1, primary_key=True)
    provider: str  # anthropic | openai | compatible
    api_key: str
    base_url: str | None = None
    auth_header: str = "bearer"  # bearer | x-api-key
    fast_model: str
    smart_model: str
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
