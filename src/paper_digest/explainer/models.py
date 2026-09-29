from datetime import UTC, datetime
from typing import Literal

from sqlmodel import Field, SQLModel


SignalKind = Literal["lookup", "missed_idea", "question"]


class PaperSummary(SQLModel, table=True):
    """The Sonnet summary + sections, kept so checks stay stable."""

    paper_id: str = Field(primary_key=True)
    data: str  # SummaryResponse JSON
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Signal(SQLModel, table=True):
    """Something the reader struggled with: where they need help."""

    id: int | None = Field(default=None, primary_key=True)
    paper_id: str = Field(index=True)
    user_id: int | None = Field(default=None, index=True)
    kind: str  # SignalKind
    text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Lookup(SQLModel, table=True):
    """A selection the reader asked to explain, with the answer they got."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    paper_id: str = Field(index=True)
    selection: str
    guess: str | None = None
    result: str  # ExplainResponse JSON
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CheckAttempt(SQLModel, table=True):
    """The reader's own summary of a section and its grade."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    paper_id: str = Field(index=True)
    section: int
    answer: str
    result: str  # CheckResponse JSON
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
