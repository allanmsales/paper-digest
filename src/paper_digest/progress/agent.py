import json

from paper_digest.clients.claude import ask_claude_once
from paper_digest.core.config import settings
from paper_digest.explainer.store import list_checks, list_signals, load_summary
from paper_digest.feed.agent import concept_graph, concept_stats
from paper_digest.progress.schemas import AssessmentDraft, AssessmentOut
from paper_digest.progress.service import progress
from paper_digest.progress.store import save_assessment


SYSTEM_PROMPT = """
You assess how well a reader understands one AI/ML research paper, using
only the evidence of what they did in a learning app. You are fair and
encouraging, but the score must follow the evidence.

Weigh the evidence like this:
- Their own summaries of paper sections and how they were graded: the
  strongest evidence of understanding.
- Quiz answers in the learning feed, per concept: right or wrong.
- Questions they asked and passages they looked up: good questions show
  engagement; many lookups on one idea show where they struggle.
- How much they covered (reading the paper, the summary, podcast, video,
  feed, checks): coverage alone is
  not understanding, but little coverage means little evidence, so keep
  the score modest and say what to do next.

Write for the reader: plain words, short sentences, no jargon. Point each
improvement at a concept from the CONCEPTS list when one fits (exact name),
and at the place in the app where they can work on it.
"""


def _evidence(paper_id: str, user_id: int) -> str:
    summary = load_summary(paper_id)
    sections = summary.sections if summary else []
    parts = []
    if summary:
        parts.append(
            f"<PAPER>\nProblem: {summary.problem}\nIdea: {summary.idea}\nResult: {summary.result}\n</PAPER>"
        )

    checks = []
    for attempt in reversed(list_checks(user_id, paper_id)):  # oldest first
        title = sections[attempt.section].title if attempt.section < len(sections) else "?"
        missed = [idea.idea for idea in attempt.result.ideas if not idea.covered]
        checks.append(
            f"- Section {title!r}: graded {attempt.result.level}. Their words: {attempt.answer!r}"
            + (f" Missed: {'; '.join(missed)}" if missed else "")
        )
    parts.append("<SECTION_SUMMARIES>\n" + ("\n".join(checks) or "none yet") + "\n</SECTION_SUMMARIES>")

    stats = concept_stats(paper_id, user_id)
    quiz = [
        f"- {name}: {item.seen}/{item.posts} posts done, quiz right {item.right}, wrong {item.wrong}"
        for name, item in stats.items()
        if item.seen
    ]
    parts.append("<FEED>\n" + ("\n".join(quiz) or "no posts done yet") + "\n</FEED>")

    signals = list_signals(paper_id, user_id)[:40]
    parts.append(
        "<ACTIVITY>\n"
        + ("\n".join(f"- ({signal.kind}) {signal.text}" for signal in signals) or "none")
        + "\n</ACTIVITY>"
    )

    covered = progress(paper_id, user_id)
    parts.append(
        "<COVERAGE>\n"
        + json.dumps(
            {
                key: round(value, 2)
                for key, value in covered.model_dump(exclude={"confirmed"}).items()
            }
            | {"confirmed": covered.confirmed}
        )
        + "\n</COVERAGE>"
    )

    _, graph = concept_graph(paper_id)
    names = list(graph.requires) if graph else list(stats)
    parts.append("<CONCEPTS>\n" + "\n".join(names) + "\n</CONCEPTS>")
    return "\n\n".join(parts)


async def assess(paper_id: str, user_id: int) -> AssessmentOut:
    draft = await ask_claude_once(
        model=settings.summary_model,
        system=SYSTEM_PROMPT,
        prompt=_evidence(paper_id, user_id),
        response_model=AssessmentDraft,
        max_tokens=4000,
    )
    # Keep the output inside its promised bounds and the map's vocabulary.
    _, graph = concept_graph(paper_id)
    known = set(graph.requires) if graph else set()
    draft.score = max(0, min(100, draft.score))
    draft.strengths = draft.strengths[:3]
    draft.improvements = draft.improvements[:5]
    for item in draft.improvements:
        if item.concept not in known:
            item.concept = None
    return save_assessment(user_id, paper_id, draft)
