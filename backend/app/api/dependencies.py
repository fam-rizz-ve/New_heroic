"""Shared API dependencies — single source of truth for use cases.

Automatically selects SQLAlchemy-backed repositories when a database URL
is configured, falling back to in-memory repositories for development.
"""

from __future__ import annotations

from app.core.interfaces.repositories import GameRepository
from app.core.use_cases.library import LibraryUseCases

_use_cases: LibraryUseCases | None = None


def get_use_cases() -> LibraryUseCases:
    """Get the shared LibraryUseCases singleton.

    If a database URL is configured in settings, uses SQLAlchemy-backed
    repositories for persistent storage. Otherwise uses in-memory
    repositories (data lost on restart).
    """
    global _use_cases
    if _use_cases is None:
        from app.core.config import settings

        if settings.database_url:
            from app.core.database import SessionFactory
            from app.core.repositories.sqlalchemy import (
                SQLAlchemyGameRepository,
                SQLAlchemyLibraryRepository,
            )

            session = SessionFactory()
            _use_cases = LibraryUseCases(
                game_repo=SQLAlchemyGameRepository(session),
                library_repo=SQLAlchemyLibraryRepository(session),
            )
        else:
            from app.core.repositories.in_memory import (
                InMemoryGameRepository,
                InMemoryLibraryRepository,
            )

            _use_cases = LibraryUseCases(
                game_repo=InMemoryGameRepository(),
                library_repo=InMemoryLibraryRepository(),
            )
    return _use_cases


def get_game_repo() -> GameRepository:
    """Get the game repository singleton."""
    return get_use_cases().game_repo
