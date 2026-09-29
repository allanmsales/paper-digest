from paper_digest.core.db import db_session
from paper_digest.video.models import VideoScript
from paper_digest.video.schemas import Narration, Storyboard


def load_storyboard(paper_id: str) -> Storyboard | None:
    with db_session() as session:
        row = session.get(VideoScript, paper_id)
        return Storyboard.model_validate_json(row.data) if row else None


def save_storyboard(paper_id: str, storyboard: Storyboard) -> None:
    # A new storyboard replaces the row, so old narration is dropped too.
    with db_session() as session:
        session.merge(VideoScript(paper_id=paper_id, data=storyboard.model_dump_json()))
        session.commit()


def narration_row(paper_id: str) -> tuple[str, Narration | None]:
    with db_session() as session:
        row = session.get(VideoScript, paper_id)
        if row is None:
            return "none", None
        timings = Narration.model_validate_json(row.timings) if row.timings else None
        return row.audio_status or "none", timings


def set_narration(paper_id: str, status: str, narration: Narration | None = None) -> None:
    with db_session() as session:
        row = session.get(VideoScript, paper_id)
        if row is not None:
            row.audio_status = status
            row.timings = narration.model_dump_json() if narration else None
            session.add(row)
            session.commit()
