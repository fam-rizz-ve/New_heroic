"""Library aggregate root."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from app.core.domain.enums import StoreSource
from app.core.domain.events import DomainEvent, GameAdded, GameRemoved
from app.core.domain.game import Game
from app.core.domain.value_objects import GameId, LibraryId


class DuplicateGameError(Exception):
    """Raised when adding a game that already exists."""


class StoreMismatchError(Exception):
    """Raised when a game's store doesn't match the library's store."""


class GameNotFoundError(Exception):
    """Raised when a game is not found in the library."""


@dataclass
class Library:
    """A collection of games from any store source (unified library).

    Invariants:
    - No duplicate games (by ID)
    - Any game from any store can be added (unified Heroic-style library)
    """

    id: LibraryId
    name: str
    store_source: StoreSource
    games: dict[GameId, Game] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    _events: list[DomainEvent] = field(default_factory=list, init=False, repr=False)

    def collect_events(self) -> list[DomainEvent]:
        """Collect and clear pending domain events."""
        events = self._events
        self._events = []
        return events

    @property
    def game_count(self) -> int:
        """Number of games in the library."""
        return len(self.games)

    def add_game(self, game: Game) -> None:
        """Add a game to the library.

        Any game can be added to any library — there is no store mismatch check.
        This enables a unified game library (Heroic-style).
        """
        if game.id in self.games:
            raise DuplicateGameError(
                f"Game '{game.title.value}' already exists in library '{self.name}'"
            )
        # Allow games from any store in the same library
        self.games[game.id] = game
        self.updated_at = datetime.now(UTC)
        self._events.append(
            GameAdded(
                event_id=uuid4(),
                game_id=game.id.value,
                title=game.title.value,
                store=game.store.value,
            )
        )

    def remove_game(self, game_id: GameId) -> Game:
        """Remove a game from the library."""
        game = self.games.pop(game_id, None)
        if game is None:
            raise GameNotFoundError(
                f"Game with id '{game_id.value}' not found in library '{self.name}'"
            )
        self.updated_at = datetime.now(UTC)
        self._events.append(
            GameRemoved(
                event_id=uuid4(),
                game_id=game.id.value,
                title=game.title.value,
            )
        )
        return game

    def get_game(self, game_id: GameId) -> Game | None:
        """Get a game by ID."""
        return self.games.get(game_id)

    def list_games(self) -> list[Game]:
        """List all games in the library."""
        return list(self.games.values())

    def find_by_title(self, title: str) -> list[Game]:
        """Find games by title (case-insensitive partial match)."""
        query = title.lower()
        return [
            game
            for game in self.games.values()
            if query in game.title.value.lower()
        ]
