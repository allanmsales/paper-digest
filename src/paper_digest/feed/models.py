from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class FeedBuild(SQLModel, table=True):
    """Progress of turning a paper's prerequisite graph into posts."""

    paper_id: str = Field(primary_key=True)
    status: str = "building"  # building | ready | error
    error: str | None = None
    concepts: str = "[]"  # JSON list of concept names, foundations first
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Post(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    paper_id: str = Field(index=True)
    concept: str
    concept_order: int  # position in the foundations-first order
    kind: str  # lesson | flip | quiz
    data: str  # PostDraft JSON


class PostView(SQLModel, table=True):
    """A post the reader finished (read, flipped or answered)."""

    id: int | None = Field(default=None, primary_key=True)
    post_id: int = Field(index=True)
    paper_id: str = Field(index=True)
    correct: bool | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
