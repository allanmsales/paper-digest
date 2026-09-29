import hashlib
from datetime import UTC, datetime

from sqlmodel import select

from paper_digest.core.db import db_session
from paper_digest.reader.models import LibraryEntry, Paper


def paper_id(paper_text: str) -> str:
    return hashlib.sha256(paper_text.encode()).hexdigest()


def save_paper(paper_text: str, source: str | None = None) -> str:
    key = paper_id(paper_text)
    with db_session() as session:
        if session.get(Paper, key) is None:
            session.add(Paper(id=key, source=source, text=paper_text))
            session.commit()
    return key


def get_paper(key: str) -> Paper | None:
    with db_session() as session:
        return session.get(Paper, key)


def record_open(user_id: int, paper_id: str, source: str | None) -> None:
    with db_session() as session:
        entry = session.get(LibraryEntry, (user_id, paper_id))
        if entry is None:
            entry = LibraryEntry(user_id=user_id, paper_id=paper_id)
        entry.source = source or entry.source
        entry.last_opened = datetime.now(UTC)
        session.add(entry)
        session.commit()


def list_library(user_id: int) -> list[LibraryEntry]:
    with db_session() as session:
        return list(
            session.exec(
                select(LibraryEntry)
                .where(LibraryEntry.user_id == user_id)
                .order_by(LibraryEntry.last_opened.desc())
            )
        )
