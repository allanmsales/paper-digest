from typing import Literal

from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema


class FlowNode(BaseModel):
    id: str = Field(description="Short identifier, e.g. 'input'.")
    label: str = Field(description="2-5 plain words shown in the box.")


class FlowEdge(BaseModel):
    source: str = Field(description="id of the node the arrow starts from.")
    target: str = Field(description="id of the node the arrow points to.")
    label: str | None = Field(default=None, description="Optional 1-3 words on the arrow.")


class FlowVisual(BaseModel):
    """Boxes and arrows: how data or steps move through the method."""

    kind: Literal["flow"]
    nodes: list[FlowNode] = Field(description="3-7 nodes.")
    edges: list[FlowEdge]
    highlight_order: list[str] = Field(
        description="Node ids in the order the narration walks through them."
    )


class EquationTerm(BaseModel):
    latex: str = Field(description="One part of the equation, in LaTeX.")
    meaning: str = Field(description="What this part does, in max 12 plain words.")


class EquationVisual(BaseModel):
    """One key equation, revealed term by term."""

    kind: Literal["equation"]
    latex: str = Field(description="The whole equation in LaTeX, simplified if needed.")
    terms: list[EquationTerm] = Field(description="2-5 parts, in reading order.")


class ExampleInput(BaseModel):
    name: str = Field(description="Python identifier, e.g. 'reward'.")
    value: float
    meaning: str = Field(description="What it stands for, max 8 plain words.")


class ExampleStep(BaseModel):
    name: str = Field(description="Python identifier for this result, e.g. 'loss'.")
    label: str = Field(description="What this step computes, max 8 plain words.")
    expression: str = Field(
        description=(
            "Arithmetic over earlier input/step names only, e.g. '(a - b) ** 2'. "
            "Allowed functions: exp, log, sqrt, abs, min, max."
        )
    )
    # Computed by us, never by the model.
    value: SkipJsonSchema[float | None] = None
    error: SkipJsonSchema[str | None] = None


class ExampleVisual(BaseModel):
    """The key math with tiny numbers, computed step by step."""

    kind: Literal["example"]
    inputs: list[ExampleInput] = Field(description="2-5 small, round numbers.")
    steps: list[ExampleStep] = Field(description="2-5 steps; the last one is the result.")
    takeaway: str = Field(description="What the final number tells us, max 20 plain words.")


class ChartBar(BaseModel):
    label: str = Field(description="1-4 words.")
    value: float


class ChartVisual(BaseModel):
    """A bar comparison of a result the paper reports."""

    kind: Literal["chart"]
    title: str
    unit: str = Field(description="What the values measure, e.g. 'accuracy %'.")
    bars: list[ChartBar] = Field(description="2-5 bars with numbers taken from the paper.")


class Scene(BaseModel):
    title: str = Field(description="3-6 words.")
    narration: str = Field(
        description="What the narrator says over this visual: 3-6 short spoken sentences."
    )
    page: int = Field(description="Paper page this scene explains.")
    visual: FlowVisual | EquationVisual | ExampleVisual | ChartVisual


class TimedSentence(BaseModel):
    text: str
    start: float
    end: float


class SceneNarration(BaseModel):
    start: float
    end: float
    sentences: list[TimedSentence]


class Narration(BaseModel):
    """Where each spoken sentence sits in the narration audio, in seconds."""

    total: float
    scenes: list[SceneNarration]


class NarrationState(BaseModel):
    status: Literal["none", "running", "ready", "failed"]
    detail: str | None = None
    narration: Narration | None = None


class Storyboard(BaseModel):
    """An animated explainer of the paper's main flow and math."""

    title: str
    scenes: list[Scene] = Field(description="5-8 scenes.")
    check_question: str = Field(
        description="One question asking the viewer to explain the main flow in their own words."
    )
