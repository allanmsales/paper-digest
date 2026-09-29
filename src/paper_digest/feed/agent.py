import asyncio
import json
import logging

from sqlmodel import select

from paper_digest.clients.claude import ask_claude_once
from paper_digest.core.config import settings
from paper_digest.core.db import db_session
from paper_digest.explainer.agent import summarize_paper
from paper_digest.explainer.store import list_signals
from paper_digest.feed.models import FeedBuild, Post, PostView
from paper_digest.feed.schemas import (
    FeedPost,
    FeedSession,
    GapConcepts,
    PostDraft,
    PostDrafts,
)
from paper_digest.reader.store import get_paper
from paper_digest.splitter.schemas import SubjectDependency
from paper_digest.splitter.service import analyze_text


logger = logging.getLogger("uvicorn.error")

SESSION_SIZE = 8

# Keeps the post-writing call (and the reader's feed) a manageable size.
MAX_CONCEPTS = 40


POSTS_PROMPT = """
You write a slow-paced learning feed, like short social media posts, that
prepares a reader to understand one research paper. Each post teaches one
prerequisite concept of that paper.

The reader is tired and reading in small bites. So:
- Everyday words, short sentences, no jargon unless it is the concept
  itself (then explain it). Plain text only, no markdown.
- Friendly and concrete: a tiny example or image beats a definition.
- Every post ends with why_it_matters: one plain line linking the concept
  to THIS paper.
- Accuracy first: when a concept name is used in a specific way in the
  PAPER, teach the paper's meaning, not a different everyday or
  software-engineering meaning of the same words.

Write exactly 2 posts per concept, in the order of the CONCEPTS list.
- The first post of each concept is a "lesson".
- The second is a "lesson", "flip" or "quiz". Across the feed, make about
  1 in 4 posts interactive ("flip" or "quiz"), spread evenly.
- quiz: 3 short options, exactly one right; wrong options should be
  plausible, not silly.
"""

GAPS_PROMPT = """
A reader is learning a research paper. Below are things they struggled
with (lookups, missed ideas, questions) and the list of prerequisite
CONCEPTS of the paper. Return the concepts that would help most with those
struggles, most helpful first (max 10). Use exact names from the list.
"""

_builds: dict[str, asyncio.Task[None]] = {}


def order_concepts(subjects: list[SubjectDependency], main: str) -> list[str]:
    """Foundations first, then concepts whose prerequisites are covered,
    ending with the paper's own new subject."""

    requires = {subject.name: set(subject.requires) for subject in subjects}
    for needs in list(requires.values()):
        for name in needs:
            requires.setdefault(name, set())
    requires.pop(main, None)

    ordered: list[str] = []
    done: set[str] = set()
    while requires:
        ready = sorted(name for name, needs in requires.items() if needs <= done)
        if not ready:  # cycle: take the least blocked concept
            ready = [min(requires, key=lambda name: len(requires[name] - done))]
        for name in ready:
            ordered.append(name)
            done.add(name)
            requires.pop(name)

    # Keep the concepts closest to the paper if there are too many.
    return ordered[-(MAX_CONCEPTS - 1):] + [main]


async def _build(paper_id: str) -> None:
    paper = get_paper(paper_id)
    if paper is None:
        raise ValueError("Unknown paper.")

    with db_session() as session:
        concepts = json.loads(session.get(FeedBuild, paper_id).concepts)

    summary = await summarize_paper(paper.text)
    if not concepts:
        analysis = await analyze_text(paper.text)
        concepts = order_concepts(analysis.subjects, analysis.new_subject)
        # Saved before writing posts, so a retry skips the slow splitter.
        with db_session() as session:
            build = session.get(FeedBuild, paper_id)
            build.concepts = json.dumps(concepts)
            session.add(build)
            session.commit()

    drafts = await ask_claude_once(
        model=settings.summary_model,
        system=POSTS_PROMPT,
        prompt=(
            f"<PAPER>\n{paper.text}\n</PAPER>\n\n"
            f"<PAPER_SUMMARY>\nProblem: {summary.problem}\nIdea: {summary.idea}\n"
            f"Result: {summary.result}\n</PAPER_SUMMARY>\n\n"
            "<CONCEPTS>\n" + "\n".join(concepts) + "\n</CONCEPTS>"
        ),
        response_model=PostDrafts,
        max_tokens=32000,
    )

    order = {name: index for index, name in enumerate(concepts)}
    with db_session() as session:
        # A rebuild replaces the posts (views of old posts are dropped too).
        for old in session.exec(select(Post).where(Post.paper_id == paper_id)):
            session.delete(old)
        for view in session.exec(select(PostView).where(PostView.paper_id == paper_id)):
            session.delete(view)
        session.add_all(
            Post(
                paper_id=paper_id,
                concept=draft.concept,
                concept_order=order.get(draft.concept, len(concepts)),
                kind=draft.kind,
                data=draft.model_dump_json(),
            )
            for draft in drafts.posts
        )
        build = session.get(FeedBuild, paper_id)
        build.status = "ready"
        session.add(build)
        session.commit()


async def _run_build(paper_id: str) -> None:
    try:
        await _build(paper_id)
    except Exception as exc:
        logger.exception("feed build failed for %s", paper_id)
        with db_session() as session:
            build = session.get(FeedBuild, paper_id)
            build.status = "error"
            build.error = str(exc)
            session.add(build)
            session.commit()
    finally:
        _builds.pop(paper_id, None)


def start_build(paper_id: str, retry: bool = False) -> str:
    """Starts building the feed once per paper; returns its status.

    A ready feed is never rebuilt (that would drop every reader's
    progress). A failed build is only restarted with `retry`, so polling
    never loops on a failing (paid) build.
    """
    with db_session() as session:
        build = session.get(FeedBuild, paper_id)
        if paper_id in _builds:
            return "building"
        if build and build.status == "ready":
            return "ready"
        if build and build.status == "error" and not retry:
            return "error"
        if build is None:
            build = FeedBuild(paper_id=paper_id)
        build.status, build.error = "building", None
        session.add(build)
        session.commit()

    _builds[paper_id] = asyncio.create_task(_run_build(paper_id))
    return "building"


async def _gap_concepts(paper_id: str, user_id: int, concepts: list[str]) -> list[str]:
    signals = list_signals(paper_id, user_id)[:30]
    if not signals:
        return []
    struggles = "\n".join(f"- ({signal.kind}) {signal.text}" for signal in signals)
    result = await ask_claude_once(
        model=settings.claude_model,
        system=GAPS_PROMPT,
        prompt=(
            f"<STRUGGLES>\n{struggles}\n</STRUGGLES>\n\n"
            "<CONCEPTS>\n" + "\n".join(concepts) + "\n</CONCEPTS>"
        ),
        response_model=GapConcepts,
        effort=None,
        fallbacks=False,
    )
    known = set(concepts)
    return [name for name in result.concepts if name in known]


async def next_session(paper_id: str, user_id: int) -> FeedSession:
    status = start_build(paper_id)
    if status != "ready":
        with db_session() as session:
            build = session.get(FeedBuild, paper_id)
            return FeedSession(status=build.status, error=build.error)

    with db_session() as session:
        build = session.get(FeedBuild, paper_id)
        concepts = json.loads(build.concepts)
        posts = list(session.exec(select(Post).where(Post.paper_id == paper_id)))
        seen_ids = set(
            session.exec(
                select(PostView.post_id).where(
                    PostView.paper_id == paper_id, PostView.user_id == user_id
                )
            )
        )

    unseen = [post for post in posts if post.id not in seen_ids]
    gaps = await _gap_concepts(paper_id, user_id, concepts) if unseen else []
    gap_rank = {name: rank for rank, name in enumerate(gaps)}

    # Your gaps first, then from the foundations up; a concept's posts stay together.
    unseen.sort(
        key=lambda post: (
            gap_rank.get(post.concept, len(gap_rank)),
            post.concept_order,
            post.id,
        )
    )

    seen_concepts = {post.concept for post in posts if post.id in seen_ids}
    return FeedSession(
        status="ready",
        posts=[
            FeedPost(id=post.id, **PostDraft.model_validate_json(post.data).model_dump())
            for post in unseen[:SESSION_SIZE]
        ],
        seen_concepts=len(seen_concepts),
        total_concepts=len({post.concept for post in posts}),
        remaining_posts=max(len(unseen) - SESSION_SIZE, 0),
    )


def record_view(post_id: int, correct: bool | None, user_id: int) -> None:
    with db_session() as session:
        post = session.get(Post, post_id)
        if post is None:
            raise ValueError("Unknown post.")
        session.add(
            PostView(post_id=post_id, paper_id=post.paper_id, user_id=user_id, correct=correct)
        )
        session.commit()
