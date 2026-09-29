from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from paper_digest.core.config import settings


def _ensure_sqlite_dir(url: str) -> None:
    prefix = "sqlite:///"
    if url.startswith(prefix):
        Path(url.removeprefix(prefix)).parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_dir(settings.database_url)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    """Creates missing tables and adds new nullable columns to existing
    ones (SQLite has no migrations here). Domain models must be imported
    first."""
    SQLModel.metadata.create_all(engine)
    _add_missing_columns()


def _add_missing_columns() -> None:
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table in SQLModel.metadata.sorted_tables:
            existing = {column["name"] for column in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing:
                    continue
                if not column.nullable:
                    raise RuntimeError(
                        f"Cannot add non-nullable column {table.name}.{column.name}"
                    )
                column_type = column.type.compile(engine.dialect)
                connection.execute(
                    text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {column_type}')
                )
    for table in SQLModel.metadata.sorted_tables:
        for index in table.indexes:
            index.create(engine, checkfirst=True)


@contextmanager
def db_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
