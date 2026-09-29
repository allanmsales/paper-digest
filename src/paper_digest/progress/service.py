from sqlmodel import select

from paper_digest.core.db import db_session
from paper_digest.explainer.store import list_checks, load_summary
from paper_digest.feed.agent import concept_graph, concept_stats, feed_fraction
from paper_digest.feed.models import Post, PostView
from paper_digest.feed.schemas import ConceptStats
from paper_digest.progress.schemas import KnowledgeMap, MapNode, NodeState, Progress
from paper_digest.progress.store import heard_fraction, latest_assessment, milestones


LEVEL_CREDIT = {"got_it": 1.0, "partly": 0.5, "not_yet": 0.0}


def check_fraction(paper_id: str, user_id: int) -> float:
    summary = load_summary(paper_id)
    if summary is None or not summary.sections:
        return 0.0
    latest: dict[int, str] = {}
    for attempt in list_checks(user_id, paper_id):  # newest first
        latest.setdefault(attempt.section, attempt.result.level)
    credit = sum(LEVEL_CREDIT[level] for level in latest.values())
    return min(1.0, credit / len(summary.sections))


def progress(paper_id: str, user_id: int) -> Progress:
    confirmed = milestones(user_id, paper_id)
    parts = {
        # Confirming counts fully; otherwise, the share of pages actually viewed.
        "reading": 1.0 if "reading" in confirmed else heard_fraction(user_id, paper_id, "reading"),
        "summary": 1.0 if "summary" in confirmed else 0.0,
        "podcast": heard_fraction(user_id, paper_id, "podcast"),
        "video": heard_fraction(user_id, paper_id, "video"),
        "feed": feed_fraction(paper_id, user_id),
        "check": check_fraction(paper_id, user_id),
    }
    return Progress(
        **parts,
        completion=sum(parts.values()) / len(parts),
        confirmed=sorted(confirmed),
    )


def node_state(stats: ConceptStats, flagged: bool) -> NodeState:
    if stats.wrong or flagged:
        return "needs_work"
    if not stats.seen:
        return "not_started"
    if stats.seen < stats.posts:
        return "learning"
    return "solid"


def flagged_concepts(paper_id: str, user_id: int) -> set[str]:
    """Concepts the latest score asked to work on, until the user answers a
    quiz on them right after that score."""
    assessment = latest_assessment(user_id, paper_id)
    if assessment is None:
        return set()
    named = {item.concept for item in assessment.improvements if item.concept}
    if not named:
        return set()
    with db_session() as session:
        fixed = set(
            session.exec(
                select(Post.concept)
                .join(PostView, PostView.post_id == Post.id)
                .where(
                    PostView.user_id == user_id,
                    PostView.paper_id == paper_id,
                    PostView.correct == True,  # noqa: E712 (SQL comparison)
                    PostView.created_at > assessment.created_at,
                    Post.concept.in_(named),
                )
            )
        )
    return named - fixed


def knowledge_map(paper_id: str, user_id: int) -> KnowledgeMap:
    """The concept graph, each node colored by how this user is doing."""
    status, graph = concept_graph(paper_id)
    if graph is None:
        return KnowledgeMap(status=status)
    stats = concept_stats(paper_id, user_id)
    flagged = flagged_concepts(paper_id, user_id)
    return KnowledgeMap(
        status="ready",
        nodes=[
            MapNode(
                name=name,
                requires=requires,
                state=node_state(stats.get(name, ConceptStats()), name in flagged),
                posts=stats.get(name, ConceptStats()).posts,
                seen=stats.get(name, ConceptStats()).seen,
                is_main=name == graph.main,
            )
            for name, requires in graph.requires.items()
        ],
    )
