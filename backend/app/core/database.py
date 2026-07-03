"""Sync SQLAlchemy database engine and session factory.

Uses synchronous SQLAlchemy to preserve backward compatibility with
existing use cases that call repository methods synchronously.
"""

from __future__ import annotations

import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""


# Build database URL: use file-based SQLite if no URL configured
_db_url = settings.database_url or "sqlite:///./data/games.db"
engine: Engine = create_engine(_db_url, echo=settings.debug)
SessionFactory: sessionmaker[Session] = sessionmaker(engine)


def get_session() -> Session:
    """Create a new database session."""
    return SessionFactory()


def init_db() -> None:
    """Create all tables.

    Ensures the data directory exists before creating tables.
    """
    # Ensure the directory for file-based databases exists
    if _db_url.startswith("sqlite:///"):
        db_path = _db_url.replace("sqlite:///", "", 1)
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    from app.models.game import GameModel  # noqa: F401
    from app.models.library import LibraryModel  # noqa: F401

    Base.metadata.create_all(engine)


def close_db() -> None:
    """Dispose of the engine, releasing all connections."""
    engine.dispose()
