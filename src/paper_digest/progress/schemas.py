from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


MediaKind = Literal["podcast", "video", "reading"]
MilestoneItem = Literal["reading", "summary"]

BUCKET_SECONDS = 5


class HeardRequest(BaseModel):
    kind: MediaKind
    buckets: list[int] = Field(max_length=2000)
    total: int = Field(gt=0, le=2000)


class MilestoneRequest(BaseModel):
    item: MilestoneItem


class Progress(BaseModel):
    """Each Learning Path step from 0 to 1; completion is their average."""

    reading: float
    summary: float
    podcast: float
    video: float
    feed: float
    check: float
    completion: float
    confirmed: list[MilestoneItem] = []


NodeState = Literal["not_started", "learning", "solid", "needs_work"]


class MapNode(BaseModel):
    name: str
    requires: list[str]
    state: NodeState
    posts: int
    seen: int
    is_main: bool


class KnowledgeMap(BaseModel):
    status: Literal["none", "building", "ready"]
    nodes: list[MapNode] = []


Place = Literal["reading", "summary", "podcast", "video", "feed", "check", "map"]


class Improvement(BaseModel):
    concept: str | None = Field(
        description="Exact name from the CONCEPTS list this is about, or null if none fits."
    )
    why: str = Field(description="What the evidence shows is missing, max 25 plain words.")
    place: Place = Field(description="Where in the app to work on it.")


class AssessmentDraft(BaseModel):
    """How well the reader understands the paper, from their own activity."""

    score: int = Field(description="0-100, from the evidence only.")
    verdict: str = Field(description="One plain sentence summing up where they stand.")
    strengths: list[str] = Field(description="Up to 3, each max 15 plain words.")
    improvements: list[Improvement] = Field(description="Up to 5, most important first.")


class AssessmentOut(AssessmentDraft):
    created_at: datetime
