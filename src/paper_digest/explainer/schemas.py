from typing import Literal

from pydantic import BaseModel, Field


class ExplainRequest(BaseModel):
    selection: str = Field(min_length=1, max_length=2000)
    page: int | None = Field(
        default=None,
        description="Page number the selection is on.",
    )
    paper_text: str = Field(min_length=1)
    guess: str | None = None


class ExplainResponse(BaseModel):
    """Explanation of text the reader selected."""

    meaning: str | None = Field(
        default=None,
        description="For a term: what it means in this paper. Max 35 words. Null for a passage.",
    )
    points: list[str] = Field(
        default_factory=list,
        description="For a passage: 2-3 plain bullets, max 15 words each. Empty for a term.",
    )
    defined_at: str | None = Field(
        default=None,
        description='Where the paper explains it, e.g. "Section 3.2, page 4". Null if nowhere.',
    )
    learn_first: list[str] = Field(
        description="At most 2 concepts to know first, 1-4 words each. Empty if none.",
    )
    guess_feedback: str | None = Field(
        default=None,
        description="One sentence on the reader's guess, or null if there was none.",
    )


class PaperRequest(BaseModel):
    paper_text: str = Field(min_length=1)
    source: str | None = Field(default=None, description="URL or file name.")


class WarmResponse(BaseModel):
    status: str
    paper_id: str


class PaperSection(BaseModel):
    """One part of the paper the reader can check their understanding of."""

    title: str = Field(description='Section title as in the paper, e.g. "Abstract", "2 Method".')
    page: int = Field(description="Page where the section starts.")
    key_ideas: list[str] = Field(
        description="2-4 ideas a reader must grasp from this section, each one plain sentence of max 20 words.",
    )


class SummaryResponse(BaseModel):
    """Three-line summary of the whole paper."""

    problem: str = Field(description="The problem the paper tackles, in everyday words.")
    idea: str = Field(description="The paper's main idea, in everyday words.")
    result: str = Field(description="What they showed or achieved, in everyday words.")
    sections: list["PaperSection"] = Field(
        description="The Abstract, then the paper's main sections in order (max 7).",
    )


class AnalogyRequest(BaseModel):
    paper_text: str = Field(min_length=1)
    subject: str = Field(
        min_length=1,
        max_length=4000,
        description="What to explain by analogy: a selection, or the paper summary.",
    )


class AnalogyMapping(BaseModel):
    """One analogy element and the paper term it stands for."""

    everyday: str = Field(description="The element in the analogy, 1-4 words.")
    term: str = Field(description="The paper's real term it stands for.")


class AnalogyResponse(BaseModel):
    """Everyday analogy mapped back to the paper's terms."""

    analogy: str = Field(
        description="Everyday-life analogy a 12-year-old gets. 2-3 short sentences.",
    )
    mapping: list[AnalogyMapping] = Field(
        description="2-4 links from analogy elements to the paper's real terms.",
    )


class CheckRequest(BaseModel):
    paper_text: str = Field(min_length=1)
    section: int = Field(default=0, ge=0, description="Index into the summary's sections.")
    answer: str = Field(min_length=1, max_length=3000)


class IdeaGrade(BaseModel):
    """Whether the reader's answer covers one key idea."""

    index: int = Field(description="Index of the key idea, starting at 0.")
    covered: bool = Field(description="True if the answer expresses this idea, in any words.")
    reread_at: str | None = Field(
        default=None,
        description='If not covered: where the paper explains it, e.g. "Section 3, page 5". Else null.',
    )


class CheckGrades(BaseModel):
    """Grades of the reader's answer against each key idea."""

    grades: list[IdeaGrade]


class CheckedIdea(BaseModel):
    idea: str
    covered: bool
    reread_at: str | None = None


class CheckResponse(BaseModel):
    level: Literal["got_it", "partly", "not_yet"]
    ideas: list[CheckedIdea]


class ThreadMessage(BaseModel):
    role: Literal["reader", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class AskRequest(BaseModel):
    paper_text: str = Field(min_length=1)
    anchor: str = Field(
        min_length=1,
        max_length=4000,
        description="What the question is about: a key idea, or a selection and its explanation.",
    )
    messages: list[ThreadMessage] = Field(
        min_length=1,
        description="The thread so far; the last message is the reader's question.",
    )


class AskResponse(BaseModel):
    """Short answer to the reader's question about one point of the paper."""

    answer: str = Field(description="2-3 short plain sentences.")
    reread_at: str | None = Field(
        default=None,
        description='Where the paper explains it, e.g. "Section 3, page 5". Null if nowhere.',
    )


class SavedLookup(BaseModel):
    id: int
    selection: str
    guess: str | None
    result: ExplainResponse


class SavedCheck(BaseModel):
    section: int
    answer: str
    result: CheckResponse
