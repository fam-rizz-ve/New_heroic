"""In-memory implementations of repository interfaces.

These are used for development, testing, and early prototyping.
Replaced with database-backed implementations in production.
"""

from __future__ import annotations

from app.core.domain.game import Game
from app.core.domain.library import Library
from app.core.domain.value_objects import GameId, LibraryId


class InMemoryGameRepository:
    """In-memory implementation of GameRepository."""

    def __init__(self) -> None:
        self._games: dict[GameId, Game] = {}

    def save(self, game: Game) -> None:
        self._games[game.id] = game

    def get(self, game_id: GameId) -> Game | None:
        return self._games.get(game_id)

    def delete(self, game_id: GameId) -> None:
        if game_id not in self._games:
            raise KeyError(f"Game with id '{game_id.value}' not found")
        del self._games[game_id]

    def list_all(self) -> list[Game]:
        return list(self._games.values())

    def find_by_title(self, query: str) -> list[Game]:
        query_lower = query.lower()
        return [
            game
            for game in self._games.values()
            if query_lower in game.title.value.lower()
        ]

    def count(self) -> int:
        return len(self._games)


class InMemoryLibraryRepository:
    """In-memory implementation of LibraryRepository."""

    def __init__(self) -> None:
        self._libraries: dict[LibraryId, Library] = {}

    def save(self, library: Library) -> None:
        self._libraries[library.id] = library

    def get(self, library_id: LibraryId) -> Library | None:
        return self._libraries.get(library_id)

    def delete(self, library_id: LibraryId) -> None:
        if library_id not in self._libraries:
            raise KeyError(f"Library with id '{library_id.value}' not found")
        del self._libraries[library_id]

    def list_all(self) -> list[Library]:
        return list(self._libraries.values())

    def count(self) -> int:
        return len(self._libraries)
