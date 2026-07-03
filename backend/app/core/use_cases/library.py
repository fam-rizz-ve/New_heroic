"""Use cases / application services for the game library.

Each use case represents a single user-facing operation.
They orchestrate domain objects and repositories following
Clean Architecture: use cases depend on domain, not on infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.domain.enums import RunnerType, StoreSource
from app.core.domain.game import Game
from app.core.domain.value_objects import GameId, GameTitle, LibraryId
from app.core.interfaces.repositories import GameRepository, LibraryRepository


@dataclass
class AddGameRequest:
    """Input for adding a game to a library."""

    title: str
    store: StoreSource
    runner: RunnerType
    description: str = ""
    cover_art_url: str = ""


@dataclass
class GameResult:
    """Output for game queries."""

    id: str
    title: str
    store: str
    runner: str
    status: str
    description: str
    cover_art_url: str
    install_path: str | None
    executable_path: str | None
    last_played: str | None
    total_play_time_seconds: int
    created_at: str  # ISO format
    updated_at: str  # ISO format


class LibraryUseCases:
    """Use cases for library and game management."""

    def __init__(
        self,
        game_repo: GameRepository,
        library_repo: LibraryRepository,
    ) -> None:
        self._game_repo = game_repo
        self._library_repo = library_repo

    def add_game_to_library(
        self, library_id: LibraryId, request: AddGameRequest
    ) -> GameResult:
        """Add a new game to a library."""
        library = self._library_repo.get(library_id)
        if library is None:
            raise ValueError(
                f"Library with id '{library_id.value}' not found"
            )

        game = Game(
            id=GameId.generate(),
            title=GameTitle(request.title),
            store=request.store,
            runner=request.runner,
            description=request.description,
            cover_art_url=request.cover_art_url,
        )

        library.add_game(game)
        self._game_repo.save(game)
        self._library_repo.save(library)
        return _game_to_result(game)

    def remove_game(self, game_id: GameId) -> None:
        """Remove a game from its library and delete it."""
        game = self._game_repo.get(game_id)
        if game is None:
            raise ValueError(
                f"Game with id '{game_id.value}' not found"
            )
        self._game_repo.delete(game_id)

    def install_game(self, game_id: GameId) -> GameResult:
        """Start installation for a game."""
        game = self._game_repo.get(game_id)
        if game is None:
            raise ValueError(
                f"Game with id '{game_id.value}' not found"
            )
        game.start_installation()
        self._game_repo.save(game)
        return _game_to_result(game)

    def complete_installation(
        self, game_id: GameId, install_path: str, executable_path: str
    ) -> GameResult:
        """Mark a game as fully installed."""
        game = self._game_repo.get(game_id)
        if game is None:
            raise ValueError(
                f"Game with id '{game_id.value}' not found"
            )
        game.complete_installation(install_path, executable_path)
        self._game_repo.save(game)
        return _game_to_result(game)

    def uninstall_game(self, game_id: GameId) -> GameResult:
        """Uninstall a game."""
        game = self._game_repo.get(game_id)
        if game is None:
            raise ValueError(
                f"Game with id '{game_id.value}' not found"
            )
        game.uninstall()
        self._game_repo.save(game)
        return _game_to_result(game)

    def launch_game(self, game_id: GameId) -> GameResult:
        """Launch a game."""
        game = self._game_repo.get(game_id)
        if game is None:
            raise ValueError(
                f"Game with id '{game_id.value}' not found"
            )
        game.launch()
        self._game_repo.save(game)
        return _game_to_result(game)

    def close_game(self, game_id: GameId) -> GameResult:
        """Close a running game."""
        game = self._game_repo.get(game_id)
        if game is None:
            raise ValueError(
                f"Game with id '{game_id.value}' not found"
            )
        game.close()
        self._game_repo.save(game)
        return _game_to_result(game)

    def get_game(self, game_id: GameId) -> GameResult | None:
        """Get details of a specific game."""
        game = self._game_repo.get(game_id)
        if game is None:
            return None
        return _game_to_result(game)

    def list_all_games(
        self,
        store: str | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> list[GameResult]:
        """List all games across all libraries with optional filters."""
        all_games = self._game_repo.list_all()

        if store:
            all_games = [g for g in all_games if g.store.value == store]
        if status:
            all_games = [g for g in all_games if g.status.value == status]
        if search:
            query = search.lower()
            all_games = [g for g in all_games if query in g.title.value.lower()]

        return [_game_to_result(g) for g in all_games]

    def list_library_games(
        self, library_id: LibraryId
    ) -> list[GameResult]:
        """List all games in a library."""
        library = self._library_repo.get(library_id)
        if library is None:
            raise ValueError(
                f"Library with id '{library_id.value}' not found"
            )
        return [_game_to_result(g) for g in library.list_games()]


def _game_to_result(game: Game) -> GameResult:
    """Convert domain Game to API-friendly GameResult."""
    return GameResult(
        id=str(game.id.value),
        title=game.title.value,
        store=game.store.value,
        runner=game.runner.value,
        status=game.status.value,
        description=game.description,
        cover_art_url=game.cover_art_url,
        install_path=game.install_path.value if game.install_path else None,
        executable_path=game.executable_path.value
        if game.executable_path
        else None,
        last_played=game.last_played.isoformat()
        if game.last_played
        else None,
        total_play_time_seconds=game.total_play_time_seconds,
        created_at=game.created_at.isoformat(),
        updated_at=game.updated_at.isoformat(),
    )
