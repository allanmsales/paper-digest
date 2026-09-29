from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class VideoScript(SQLModel, table=True):
    paper_id: str = Field(primary_key=True)
    data: str  # Storyboard JSON, as the model wrote it
    # Narration: none | running | ready | failed. Reset when the storyboard changes.
    audio_status: str | None = None
    timings: str | None = None  # Narration JSON
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
