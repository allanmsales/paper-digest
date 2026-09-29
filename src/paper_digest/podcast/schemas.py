from typing import Literal

from pydantic import BaseModel, Field


class Line(BaseModel):
    speaker: Literal["host", "author"]
    text: str


class Script(BaseModel):
    """An interview between a podcast host and the paper's author."""

    title: str
    lines: list[Line] = Field(description="Alternating host/author turns, host first.")


class AudioState(BaseModel):
    status: Literal["none", "running", "ready", "failed"]
    detail: str | None = None
