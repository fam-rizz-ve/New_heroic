"""Shared API dependencies — single source of truth for use cases."""

from __future__ import annotations

from app.core.use_cases.library import LibraryUseCases

_use_cases: LibraryUseCases | None = None


def get_use_cases() -> LibraryUseCases:
    """Get the shared LibraryUseCases singleton.

    All API modules use this function so they share the same
    in-memory repositories within a single process.
    """
    global _use_cases
    if _use_cases is None:
        from app.core.repositories.in_memory import (
            InMemoryGameRepository,
            InMemoryLibraryRepository,
        )

        _use_cases = LibraryUseCases(
            game_repo=InMemoryGameRepository(),
            library_repo=InMemoryLibraryRepository(),
        )
    return _use_cases
