from sqlmodel import select

from paper_digest.core.db import db_session
from paper_digest.explainer.models import PaperSummary, Signal, SignalKind
from paper_digest.explainer.schemas import SummaryResponse


def load_summary(paper_id: str) -> SummaryResponse | None:
    with db_session() as session:
        row = session.get(PaperSummary, paper_id)
        return SummaryResponse.model_validate_json(row.data) if row else None


def save_summary(paper_id: str, summary: SummaryResponse) -> None:
    with db_session() as session:
        session.merge(PaperSummary(paper_id=paper_id, data=summary.model_dump_json()))
        session.commit()


def add_signals(paper_id: str, kind: SignalKind, texts: list[str]) -> None:
    if not texts:
        return
    with db_session() as session:
        session.add_all(Signal(paper_id=paper_id, kind=kind, text=text) for text in texts)
        session.commit()


def list_signals(paper_id: str) -> list[Signal]:
    with db_session() as session:
        return list(
            session.exec(
                select(Signal)
                .where(Signal.paper_id == paper_id)
                .order_by(Signal.created_at.desc())
            )
        )
