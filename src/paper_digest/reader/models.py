from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Paper(SQLModel, table=True):
    # sha256 of the extracted text: the same PDF always maps to one paper.
    id: str = Field(primary_key=True)
    source: str | None = None
    text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
