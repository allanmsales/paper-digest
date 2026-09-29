from paper_digest.core.db import db_session
from paper_digest.podcast.models import AudioStatus, Podcast
from paper_digest.podcast.schemas import Script


def load_script(paper_id: str) -> Script | None:
    with db_session() as session:
        row = session.get(Podcast, paper_id)
        return Script.model_validate_json(row.script) if row else None


def save_script(paper_id: str, script: Script) -> None:
    with db_session() as session:
        session.merge(Podcast(paper_id=paper_id, script=script.model_dump_json()))
        session.commit()


def audio_status(paper_id: str) -> AudioStatus:
    with db_session() as session:
        row = session.get(Podcast, paper_id)
        return row.audio_status if row else "none"


def set_audio_status(paper_id: str, status: AudioStatus) -> None:
    with db_session() as session:
        row = session.get(Podcast, paper_id)
        if row is not None:
            row.audio_status = status
            session.add(row)
            session.commit()
