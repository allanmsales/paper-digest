import asyncio
import json
import logging

from sqlmodel import select

from paper_digest.clients.claude import ask_claude_once
from paper_digest.core.config import settings
from paper_digest.core.db import db_session
from paper_digest.explainer.agent import summarize_paper
from paper_digest.feed.models import FeedBuild, FeedSelection, Post, PostView
from paper_digest.feed.schemas import (
    ConceptGraph,
    ConceptLinks,
    ConceptStats,
    FeedPost,
    FeedSession,
    PostDraft,
    PostDrafts,
)
from paper_digest.reader.store import get_paper
from paper_digest.splitter.schemas import SubjectDependency
from paper_digest.splitter.service import analyze_text


logger = logging.getLogger("uvicorn.error")


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
        graph = acyclic_graph(
            concepts, {subject.name: subject.requires for subject in analysis.subjects}
        )
        # Saved before writing posts, so a retry skips the slow splitter.
        with db_session() as session:
            build = session.get(FeedBuild, paper_id)
            build.concepts = json.dumps(concepts)
            build.graph = graph.model_dump_json()
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


def acyclic_graph(concepts: list[str], requires: dict[str, list[str]]) -> ConceptGraph:
    """Keeps only links between known concepts that point to an earlier one
    in the foundations-first order, so the graph is always acyclic."""
    position = {name: index for index, name in enumerate(concepts)}
    return ConceptGraph(
        main=concepts[-1],
        requires={
            name: sorted(
                {
                    need
                    for need in requires.get(name, [])
                    if need in position and position[need] < position[name]
                },
                key=position.__getitem__,
            )
            for name in concepts
        },
    )


LINKS_PROMPT = """
You map how the concepts needed to read one AI/ML paper build on each
other. For every concept in the list, give the concepts from the same list
it directly builds on (its immediate prerequisites, not all ancestors).
Foundations build on nothing. The list is ordered foundations first, and
the last concept is the paper's own new idea. Use exact names from the list.
"""

_graphs: dict[str, asyncio.Task[None]] = {}


async def _infer_graph(paper_id: str, concepts: list[str]) -> None:
    """For feeds built before graphs were saved: links among the existing
    concepts, so the map matches the feed's posts."""
    try:
        result = await ask_claude_once(
            model=settings.claude_model,
            system=LINKS_PROMPT,
            prompt="<CONCEPTS>\n" + "\n".join(concepts) + "\n</CONCEPTS>",
            response_model=ConceptLinks,
            max_tokens=8000,
            effort=None,
            fallbacks=False,
        )
        graph = acyclic_graph(concepts, {link.concept: link.requires for link in result.links})
        with db_session() as session:
            build = session.get(FeedBuild, paper_id)
            build.graph = graph.model_dump_json()
            session.add(build)
            session.commit()
    except Exception:
        logger.exception("concept graph failed for %s", paper_id)
    finally:
        _graphs.pop(paper_id, None)


def concept_graph(paper_id: str) -> tuple[str, ConceptGraph | None]:
    """The paper's concept graph and its status: ready, building or none
    (no feed yet). Starts inferring it for older feeds."""
    with db_session() as session:
        build = session.get(FeedBuild, paper_id)
        if build is None or not json.loads(build.concepts):
            return ("building" if build and build.status == "building" else "none"), None
        if build.graph:
            return "ready", ConceptGraph.model_validate_json(build.graph)
        concepts = json.loads(build.concepts)
    if paper_id not in _graphs:
        _graphs[paper_id] = asyncio.create_task(_infer_graph(paper_id, concepts))
    return "building", None


def concept_stats(paper_id: str, user_id: int) -> dict[str, ConceptStats]:
    """Per concept: how many posts it has, and how many this user finished
    or answered right/wrong."""
    with db_session() as session:
        posts = list(session.exec(select(Post).where(Post.paper_id == paper_id)))
        views = list(
            session.exec(
                select(PostView).where(
                    PostView.paper_id == paper_id, PostView.user_id == user_id
                )
            )
        )
    latest = {view.post_id: view for view in sorted(views, key=lambda view: view.created_at)}
    stats: dict[str, ConceptStats] = {}
    for post in posts:
        item = stats.setdefault(post.concept, ConceptStats())
        item.posts += 1
        view = latest.get(post.id)
        if view is None:
            continue
        item.seen += 1
        if view.correct is True:
            item.right += 1
        elif view.correct is False:
            item.wrong += 1
    return stats


def _select_posts(posts: list[Post]) -> list[int]:
    """Picks the user's feed once: one post for every concept of the paper,
    foundations first, so the whole knowledge map is covered."""
    by_concept: dict[str, list[Post]] = {}
    for post in sorted(posts, key=lambda post: post.id):
        by_concept.setdefault(post.concept, []).append(post)
    concepts = sorted(by_concept, key=lambda name: by_concept[name][0].concept_order)
    # Alternate reading a lesson with doing something (a quiz, else a flip).
    preference = [["lesson", "quiz", "flip"], ["quiz", "flip", "lesson"]]
    picked = []
    for index, name in enumerate(concepts):
        options = by_concept[name]
        rank = preference[index % 2]
        picked.append(min(options, key=lambda post: rank.index(post.kind)).id)
    return picked


def _selection(paper_id: str, user_id: int) -> list[int]:
    with db_session() as session:
        posts = list(session.exec(select(Post).where(Post.paper_id == paper_id)))
        row = session.get(FeedSelection, (user_id, paper_id))
    concept_of = {post.id: post.concept for post in posts}
    if row is not None:
        ids = json.loads(row.post_ids)
        # Pick again if the feed was rebuilt (posts replaced) or the saved
        # pick doesn't cover every concept (e.g. an older, shorter feed).
        if all(post_id in concept_of for post_id in ids) and {
            concept_of[post_id] for post_id in ids
        } == set(concept_of.values()):
            return ids
    ids = _select_posts(posts)
    with db_session() as session:
        session.merge(FeedSelection(user_id=user_id, paper_id=paper_id, post_ids=json.dumps(ids)))
        session.commit()
    return ids


def _done_ids(paper_id: str, user_id: int) -> set[int]:
    with db_session() as session:
        return set(
            session.exec(
                select(PostView.post_id).where(
                    PostView.paper_id == paper_id, PostView.user_id == user_id
                )
            )
        )


async def next_session(paper_id: str, user_id: int) -> FeedSession:
    status = start_build(paper_id)
    if status != "ready":
        with db_session() as session:
            build = session.get(FeedBuild, paper_id)
            return FeedSession(status=build.status, error=build.error)

    ids = _selection(paper_id, user_id)
    done = _done_ids(paper_id, user_id)
    with db_session() as session:
        posts = {post.id: post for post in session.exec(select(Post).where(Post.id.in_(ids)))}
    feed = [
        FeedPost(
            id=post_id,
            done=post_id in done,
            **PostDraft.model_validate_json(posts[post_id].data).model_dump(),
        )
        for post_id in ids
    ]
    return FeedSession(status="ready", posts=feed, done=sum(post.done for post in feed))


def feed_fraction(paper_id: str, user_id: int) -> float:
    """Share of this user's feed they finished; 0 before it was opened."""
    with db_session() as session:
        row = session.get(FeedSelection, (user_id, paper_id))
    if row is None:
        return 0.0
    ids = json.loads(row.post_ids)
    if not ids:
        return 0.0
    return len(set(ids) & _done_ids(paper_id, user_id)) / len(ids)


def record_view(post_id: int, correct: bool | None, user_id: int) -> None:
    with db_session() as session:
        post = session.get(Post, post_id)
        if post is None:
            raise ValueError("Unknown post.")
        session.add(
            PostView(post_id=post_id, paper_id=post.paper_id, user_id=user_id, correct=correct)
        )
        session.commit()
