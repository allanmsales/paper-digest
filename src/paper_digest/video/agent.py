import asyncio

from paper_digest.clients.claude import ask_claude_once
from paper_digest.core.config import settings
from paper_digest.reader.store import get_paper
from paper_digest.video.calculator import evaluate
from paper_digest.video.schemas import ExampleVisual, Storyboard
from paper_digest.video.store import load_storyboard, save_storyboard


SYSTEM_PROMPT = """
You storyboard a short animated explainer video, in the style of
3Blue1Brown, that helps a viewer understand one AI/ML research paper,
shown below. The goal is understanding the paper's main flow and math,
not coding it.

The viewer is smart but does NOT know this field. Always:

- Pick the 5-8 scenes that matter most, building up in order: the problem,
  the method's flow, the key math, a worked example with tiny numbers, and
  what the results show.
- Each scene has exactly one visual:
  - flow: boxes and arrows for how data or steps move through the method.
  - equation: the one or two equations that carry the idea, simplified if
    needed, split into parts with a plain meaning for each.
  - example: the same math with small round numbers. Give the inputs and
    each step as an arithmetic expression over earlier names; we compute
    the values, so never write the results yourself.
  - chart: a bar comparison using numbers the paper reports. All bars
    share one unit; never mix measures (e.g. accuracy and error rate) in
    one chart.
- Use at least one flow, one equation and one example.
- Narration is spoken over the visual: everyday words, short complete
  sentences, one idea per sentence. Point at what is on screen ("the
  first box", "this term"). Never read LaTeX aloud; say what it means.
- If a key term must appear, name it once and explain it in the same
  sentence. Never use abbreviations like FPR or MPC in labels or
  narration; say what they mean.
- Name specific models, datasets or benchmarks only when the scene cannot
  be understood without them; say "a large language model" instead.
- Stay on this paper; never branch into topics it does not need.
- Plain text only in labels and narration, no markdown.

The full paper follows. Page markers look like "--- PAGE n ---".
"""

TASK = "Write the storyboard."

_storyboards: dict[str, asyncio.Task[Storyboard]] = {}


async def storyboard(paper_id: str) -> Storyboard:
    # One generation per paper, even with concurrent requests.
    if paper_id not in _storyboards:
        _storyboards[paper_id] = asyncio.create_task(_load_or_create(paper_id))
    try:
        return compute_examples(await asyncio.shield(_storyboards[paper_id]))
    except Exception:
        # Let the next request retry instead of caching the failure.
        _storyboards.pop(paper_id, None)
        raise


async def _load_or_create(paper_id: str) -> Storyboard:
    board = load_storyboard(paper_id)
    if board is None:
        paper = get_paper(paper_id)
        if paper is None:
            raise LookupError(f"Unknown paper {paper_id}")
        board = await ask_claude_once(
            model=settings.summary_model,
            system=SYSTEM_PROMPT + f"\n<PAPER>\n{paper.text}\n</PAPER>",
            prompt=TASK,
            response_model=Storyboard,
            max_tokens=16000,
        )
        save_storyboard(paper_id, board)
    return board


def compute_examples(board: Storyboard) -> Storyboard:
    """Fills each worked-example step's value with our own arithmetic."""
    board = board.model_copy(deep=True)
    for scene in board.scenes:
        if not isinstance(scene.visual, ExampleVisual):
            continue
        names = {item.name: item.value for item in scene.visual.inputs}
        for step in scene.visual.steps:
            try:
                step.value = evaluate(step.expression, names)
                names[step.name] = step.value
            except Exception as exc:
                step.error = str(exc)
    return board
