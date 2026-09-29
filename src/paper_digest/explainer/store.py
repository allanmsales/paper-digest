from sqlmodel import select

from paper_digest.core.db import db_session
from paper_digest.explainer.models import CheckAttempt, Lookup, PaperSummary, Signal, SignalKind
from paper_digest.explainer.schemas import (
    CheckResponse,
    ExplainResponse,
    SavedCheck,
    SavedLookup,
    SummaryResponse,
)


def load_summary(paper_id: str) -> SummaryResponse | None:
    with db_session() as session:
        row = session.get(PaperSummary, paper_id)
        return SummaryResponse.model_validate_json(row.data) if row else None


def save_summary(paper_id: str, summary: SummaryResponse) -> None:
    with db_session() as session:
        session.merge(PaperSummary(paper_id=paper_id, data=summary.model_dump_json()))
        session.commit()


def add_signals(paper_id: str, user_id: int, kind: SignalKind, texts: list[str]) -> None:
    if not texts:
        return
    with db_session() as session:
        session.add_all(
            Signal(paper_id=paper_id, user_id=user_id, kind=kind, text=text) for text in texts
        )
        session.commit()


def list_signals(paper_id: str, user_id: int) -> list[Signal]:
    with db_session() as session:
        return list(
            session.exec(
                select(Signal)
                .where(Signal.paper_id == paper_id, Signal.user_id == user_id)
                .order_by(Signal.created_at.desc())
            )
        )


def save_lookup(
    user_id: int, paper_id: str, selection: str, guess: str | None, result: ExplainResponse
) -> None:
    with db_session() as session:
        session.add(
            Lookup(
                user_id=user_id,
                paper_id=paper_id,
                selection=selection,
                guess=guess,
                result=result.model_dump_json(),
            )
        )
        session.commit()


def list_lookups(user_id: int, paper_id: str) -> list[SavedLookup]:
    with db_session() as session:
        rows = session.exec(
            select(Lookup)
            .where(Lookup.user_id == user_id, Lookup.paper_id == paper_id)
            .order_by(Lookup.created_at.desc())
        )
        return [
            SavedLookup(
                id=row.id,
                selection=row.selection,
                guess=row.guess,
                result=ExplainResponse.model_validate_json(row.result),
            )
            for row in rows
        ]


def save_check(
    user_id: int, paper_id: str, section: int, answer: str, result: CheckResponse
) -> None:
    with db_session() as session:
        session.add(
            CheckAttempt(
                user_id=user_id,
                paper_id=paper_id,
                section=section,
                answer=answer,
                result=result.model_dump_json(),
            )
        )
        session.commit()


def list_checks(user_id: int, paper_id: str) -> list[SavedCheck]:
    with db_session() as session:
        rows = session.exec(
            select(CheckAttempt)
            .where(CheckAttempt.user_id == user_id, CheckAttempt.paper_id == paper_id)
            .order_by(CheckAttempt.created_at.desc())
        )
        return [
            SavedCheck(
                section=row.section,
                answer=row.answer,
                result=CheckResponse.model_validate_json(row.result),
            )
            for row in rows
        ]
