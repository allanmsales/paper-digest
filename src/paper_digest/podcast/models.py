from datetime import UTC, datetime
from typing import Literal

from sqlmodel import Field, SQLModel


AudioStatus = Literal["none", "running", "ready", "failed"]


class Podcast(SQLModel, table=True):
    paper_id: str = Field(primary_key=True)
    script: str  # Script JSON
    audio_status: str = "none"  # AudioStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
