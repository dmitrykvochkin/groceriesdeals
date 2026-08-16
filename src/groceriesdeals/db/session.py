"""Database engine and session helpers."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlmodel import Session, create_engine

from groceriesdeals.config import get_settings

_settings = get_settings()
engine = create_engine(_settings.database_url, echo=False)


@contextmanager
def get_session() -> Iterator[Session]:
    """Yield a SQLModel session that commits on success and rolls back on error."""
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
