import hashlib

from paper_digest.core.db import db_session
from paper_digest.reader.models import Paper


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
