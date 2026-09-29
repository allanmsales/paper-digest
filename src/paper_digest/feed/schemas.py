from typing import Literal

from pydantic import BaseModel, Field


PostKind = Literal["lesson", "flip", "quiz"]


class PostDraft(BaseModel):
    concept: str = Field(description="Exact concept name from the CONCEPTS list.")
    kind: PostKind
    title: str = Field(description="Catchy, plain title, max 8 words.")
    body: str = Field(
        description="lesson: the lesson, max 40 words. flip: the front (a question or prompt). quiz: the question.",
    )
    back: str | None = Field(default=None, description="flip only: the answer, max 30 words. Else null.")
    options: list[str] = Field(
        default_factory=list,
        description="quiz only: exactly 3 short options. Else empty.",
    )
    answer_index: int | None = Field(default=None, description="quiz only: index of the right option. Else null.")
    why_it_matters: str = Field(description="One plain line: why this matters for THIS paper.")


class PostDrafts(BaseModel):
    posts: list[PostDraft]


class GapConcepts(BaseModel):
    concepts: list[str] = Field(
        description="Concept names from the list, most relevant to the reader's struggles first.",
    )


class FeedPost(PostDraft):
    id: int


class FeedSession(BaseModel):
    status: Literal["building", "ready", "error"]
    error: str | None = None
    posts: list[FeedPost] = Field(default_factory=list)
    seen_concepts: int = 0
    total_concepts: int = 0
    remaining_posts: int = 0


class ViewRequest(BaseModel):
    post_id: int
    correct: bool | None = None
