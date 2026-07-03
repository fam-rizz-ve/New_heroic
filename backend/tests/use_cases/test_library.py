"""Tests for library use cases."""

from uuid import UUID

import pytest

from app.core.domain.enums import RunnerType, StoreSource
from app.core.domain.library import Library
from app.core.domain.value_objects import GameId, LibraryId
from app.core.repositories.in_memory import (
    InMemoryGameRepository,
    InMemoryLibraryRepository,
)
from app.core.use_cases.library import AddGameRequest, LibraryUseCases


@pytest.fixture
def use_cases() -> LibraryUseCases:
    """Create a fresh LibraryUseCases fixture with isolated repos."""
    return LibraryUseCases(
        game_repo=InMemoryGameRepository(),
        library_repo=InMemoryLibraryRepository(),
    )


@pytest.fixture
def library(use_cases: LibraryUseCases) -> Library:
    """Create and save a library fixture."""
    lib = Library(
        id=LibraryId.generate(),
        name="Test Library",
        store_source=StoreSource.LOCAL,
    )
    use_cases._library_repo.save(lib)
    return lib


class TestAddGameToLibrary:
    """Tests for adding a game to a library via use cases."""

    def test_add_game_success(
        self, use_cases: LibraryUseCases, library: Library
    ) -> None:
        """Adding a valid game should return a GameResult with correct title."""
        request = AddGameRequest(
            title="New Game",
            store=StoreSource.LOCAL,
            runner=RunnerType.NATIVE,
        )
        result = use_cases.add_game_to_library(library.id, request)
        assert result.title == "New Game"
        assert result.status == "not_installed"
        assert result.created_at is not None

    def test_add_game_with_description(
        self, use_cases: LibraryUseCases, library: Library
    ) -> None:
        """Adding a game with description should preserve it."""
        request = AddGameRequest(
            title="Game with Desc",
            store=StoreSource.LOCAL,
            runner=RunnerType.NATIVE,
            description="A cool game",
        )
        result = use_cases.add_game_to_library(library.id, request)
        assert result.description == "A cool game"

    def test_add_game_nonexistent_library(
        self, use_cases: LibraryUseCases
    ) -> None:
        """Adding a game to a non-existent library should raise ValueError."""
        request = AddGameRequest(
            title="Orphan Game",
            store=StoreSource.LOCAL,
            runner=RunnerType.NATIVE,
        )
        with pytest.raises(ValueError, match="not found"):
            use_cases.add_game_to_library(LibraryId.generate(), request)


class TestRemoveGame:
    """Tests for removing a game via use cases."""

    def test_remove_existing_game(
        self, use_cases: LibraryUseCases, library: Library
    ) -> None:
        """Removing an existing game should succeed."""
        request = AddGameRequest(
            title="Game to Remove",
            store=StoreSource.LOCAL,
            runner=RunnerType.NATIVE,
        )
        result = use_cases.add_game_to_library(library.id, request)
        game_id = GameId(UUID(result.id))
        use_cases.remove_game(game_id)
        assert use_cases.get_game(game_id) is None

    def test_remove_nonexistent_raises(
        self, use_cases: LibraryUseCases
    ) -> None:
        """Removing a non-existent game should raise ValueError."""
        with pytest.raises(ValueError, match="not found"):
            use_cases.remove_game(GameId.generate())


class TestGameLifecycle:
    """Tests for the full game lifecycle via use cases."""

    def test_full_lifecycle(
        self, use_cases: LibraryUseCases, library: Library
    ) -> None:
        """Test the complete install → launch → close → uninstall cycle."""
        # Add game
        request = AddGameRequest(
            title="Lifecycle Game",
            store=StoreSource.LOCAL,
            runner=RunnerType.NATIVE,
        )
        result = use_cases.add_game_to_library(library.id, request)
        game_id = GameId(UUID(result.id))

        # Install
        result = use_cases.install_game(game_id)
        assert result.status == "installing"

        # Complete installation
        result = use_cases.complete_installation(game_id, "/path", "/exe")
        assert result.status == "installed"
        assert result.install_path == "/path"

        # Launch
        result = use_cases.launch_game(game_id)
        assert result.status == "running"

        # Close
        result = use_cases.close_game(game_id)
        assert result.status == "installed"

        # Uninstall
        result = use_cases.uninstall_game(game_id)
        assert result.status == "not_installed"


class TestGetGame:
    """Tests for getting game details via use cases."""

    def test_get_existing_game(
        self, use_cases: LibraryUseCases, library: Library
    ) -> None:
        """Getting an existing game should return its details."""
        request = AddGameRequest(
            title="Visible Game",
            store=StoreSource.LOCAL,
            runner=RunnerType.NATIVE,
        )
        use_cases.add_game_to_library(library.id, request)
        # Get the game from the library
        games = use_cases.list_library_games(library.id)
        assert len(games) == 1
        assert games[0].title == "Visible Game"

    def test_get_nonexistent_game(
        self, use_cases: LibraryUseCases
    ) -> None:
        """Getting a non-existent game should return None."""
        result = use_cases.get_game(GameId.generate())
        assert result is None

    def test_list_games_in_library(
        self, use_cases: LibraryUseCases, library: Library
    ) -> None:
        """Listing games should return all games in the library."""
        request = AddGameRequest(
            title="Game 1",
            store=StoreSource.LOCAL,
            runner=RunnerType.NATIVE,
        )
        use_cases.add_game_to_library(library.id, request)

        request2 = AddGameRequest(
            title="Game 2",
            store=StoreSource.LOCAL,
            runner=RunnerType.NATIVE,
        )
        use_cases.add_game_to_library(library.id, request2)

        games = use_cases.list_library_games(library.id)
        assert len(games) == 2

    def test_list_games_nonexistent_library(
        self, use_cases: LibraryUseCases
    ) -> None:
        """Listing games for a non-existent library should raise ValueError."""
        with pytest.raises(ValueError, match="not found"):
            use_cases.list_library_games(LibraryId.generate())
