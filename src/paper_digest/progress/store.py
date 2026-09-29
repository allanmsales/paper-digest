import json

from paper_digest.core.db import db_session
from sqlmodel import select

from paper_digest.progress.models import Assessment, MediaProgress, Milestone
from paper_digest.progress.schemas import AssessmentDraft, AssessmentOut, MediaKind, MilestoneItem


def add_heard(user_id: int, paper_id: str, kind: MediaKind, buckets: list[int], total: int) -> None:
    with db_session() as session:
        row = session.get(MediaProgress, (user_id, paper_id, kind))
        if row is None:
            row = MediaProgress(user_id=user_id, paper_id=paper_id, kind=kind)
        heard = set(json.loads(row.heard)) | {bucket for bucket in buckets if 0 <= bucket < total}
        row.heard = json.dumps(sorted(heard))
        row.total = total
        session.add(row)
        session.commit()


def heard_fraction(user_id: int, paper_id: str, kind: MediaKind) -> float:
    with db_session() as session:
        row = session.get(MediaProgress, (user_id, paper_id, kind))
        if row is None or row.total == 0:
            return 0.0
        return min(1.0, len(json.loads(row.heard)) / row.total)


def add_milestone(user_id: int, paper_id: str, item: MilestoneItem) -> None:
    with db_session() as session:
        if session.get(Milestone, (user_id, paper_id, item)) is None:
            session.add(Milestone(user_id=user_id, paper_id=paper_id, item=item))
            session.commit()


def milestones(user_id: int, paper_id: str) -> set[str]:
    with db_session() as session:
        return set(
            session.exec(
                select(Milestone.item).where(
                    Milestone.user_id == user_id, Milestone.paper_id == paper_id
                )
            )
        )


def save_assessment(user_id: int, paper_id: str, draft: AssessmentDraft) -> AssessmentOut:
    row = Assessment(
        user_id=user_id, paper_id=paper_id, score=draft.score, data=draft.model_dump_json()
    )
    with db_session() as session:
        session.add(row)
        session.commit()
        session.refresh(row)
    return AssessmentOut(**draft.model_dump(), created_at=row.created_at)


def latest_assessment(user_id: int, paper_id: str) -> AssessmentOut | None:
    with db_session() as session:
        row = session.exec(
            select(Assessment)
            .where(Assessment.user_id == user_id, Assessment.paper_id == paper_id)
            .order_by(Assessment.created_at.desc())
        ).first()
    if row is None:
        return None
    return AssessmentOut(
        **AssessmentDraft.model_validate_json(row.data).model_dump(), created_at=row.created_at
    )
