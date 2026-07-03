"""Repository interfaces for the game library domain.

Uses typing.Protocol for structural typing (Duck Typing) rather than
abc.ABC to avoid coupling domain abstractions to a specific inheritance
hierarchy. This follows Clean Architecture's Dependency Rule.
"""

from __future__ import annotations

from typing import Protocol

from app.core.domain.game import Game
from app.core.domain.library import Library
from app.core.domain.value_objects import GameId, LibraryId


class GameRepository(Protocol):
    """Interface for game persistence."""

    def save(self, game: Game) -> None:
        """Persist a game (create or update)."""
        ...

    def get(self, game_id: GameId) -> Game | None:
        """Get a game by its ID. Returns None if not found."""
        ...

    def delete(self, game_id: GameId) -> None:
        """Delete a game by its ID. Raises KeyError if not found."""
        ...

    def list_all(self) -> list[Game]:
        """List all games."""
        ...

    def find_by_title(self, query: str) -> list[Game]:
        """Find games whose title contains the query (case-insensitive)."""
        ...

    def count(self) -> int:
        """Return the total number of games."""
        ...


class LibraryRepository(Protocol):
    """Interface for library persistence."""

    def save(self, library: Library) -> None:
        """Persist a library (create or update)."""
        ...

    def get(self, library_id: LibraryId) -> Library | None:
        """Get a library by its ID. Returns None if not found."""
        ...

    def delete(self, library_id: LibraryId) -> None:
        """Delete a library by its ID. Raises KeyError if not found."""
        ...

    def list_all(self) -> list[Library]:
        """List all libraries."""
        ...

    def count(self) -> int:
        """Return the total number of libraries."""
        ...
