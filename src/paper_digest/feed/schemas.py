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


class FeedPost(PostDraft):
    id: int
    done: bool = False


class FeedSession(BaseModel):
    """The user's whole feed for a paper: one fixed set of posts."""

    status: Literal["building", "ready", "error"]
    error: str | None = None
    posts: list[FeedPost] = Field(default_factory=list)
    done: int = 0


class ViewRequest(BaseModel):
    post_id: int
    correct: bool | None = None


class ConceptStats(BaseModel):
    posts: int = 0
    seen: int = 0
    right: int = 0
    wrong: int = 0


class ConceptLink(BaseModel):
    concept: str = Field(description="Exact concept name from the list.")
    requires: list[str] = Field(
        description="Exact names from the list this concept directly builds on. Empty for foundations."
    )


class ConceptLinks(BaseModel):
    """Direct prerequisite links among the paper's concepts."""

    links: list[ConceptLink]


class ConceptGraph(BaseModel):
    """The paper's concept hierarchy: an acyclic graph, foundations first."""

    main: str
    requires: dict[str, list[str]]
