from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class MediaProgress(SQLModel, table=True):
    """Which parts of the podcast or video this user actually played."""

    user_id: int = Field(primary_key=True)
    paper_id: str = Field(primary_key=True)
    kind: str = Field(primary_key=True)  # podcast | video | reading
    # JSON list of played 5-second buckets (reading: pages read)
    heard: str = "[]"
    total: int = 0  # buckets in the whole recording (reading: pages)


class Milestone(SQLModel, table=True):
    """Something the user confirmed doing, e.g. reading the paper."""

    user_id: int = Field(primary_key=True)
    paper_id: str = Field(primary_key=True)
    item: str = Field(primary_key=True)  # reading | summary
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Assessment(SQLModel, table=True):
    """The agent's score of how well this user understands the paper."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    paper_id: str = Field(index=True)
    score: int
    data: str  # AssessmentDraft JSON
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
