from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Paper(SQLModel, table=True):
    # sha256 of the extracted text: the same PDF always maps to one paper.
    id: str = Field(primary_key=True)
    source: str | None = None
    text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LibraryEntry(SQLModel, table=True):
    """A paper a user opened; the home page lists them to continue reading."""

    user_id: int = Field(primary_key=True)
    paper_id: str = Field(primary_key=True)
    source: str | None = None
    last_opened: datetime = Field(default_factory=lambda: datetime.now(UTC))
