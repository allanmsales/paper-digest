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
    kind: str  # SignalKind
    text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
