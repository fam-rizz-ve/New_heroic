"""Tests for the Library aggregate."""

import pytest

from app.core.domain.enums import RunnerType, StoreSource
from app.core.domain.game import Game
from app.core.domain.library import (
    DuplicateGameError,
    GameNotFoundError,
    Library,
)
from app.core.domain.value_objects import GameId, GameTitle, LibraryId


@pytest.fixture
def library() -> Library:
    """Create a fresh Library fixture for testing."""
    return Library(
        id=LibraryId.generate(),
        name="Test Library",
        store_source=StoreSource.LOCAL,
    )


@pytest.fixture
def local_game() -> Game:
    """Create a local store game fixture."""
    return Game(
        id=GameId.generate(),
        title=GameTitle("Test Game"),
        store=StoreSource.LOCAL,
        runner=RunnerType.NATIVE,
    )


@pytest.fixture
def epic_game() -> Game:
    """Create an Epic store game fixture."""
    return Game(
        id=GameId.generate(),
        title=GameTitle("Epic Game"),
        store=StoreSource.EPIC,
        runner=RunnerType.WINE,
    )


class TestLibraryInitialState:
    """Tests for the initial state of a Library."""

    def test_starts_empty(self, library: Library) -> None:
        """A new library should have no games."""
        assert library.game_count == 0
        assert library.list_games() == []

    def test_no_events_initially(self, library: Library) -> None:
        """A new library should have no pending events."""
        assert library.collect_events() == []


class TestLibraryAddGame:
    """Tests for adding games to a library."""

    def test_add_game_success(self, library: Library, local_game: Game) -> None:
        """Adding a game should increase game count."""
        library.add_game(local_game)
        assert library.game_count == 1
        assert library.get_game(local_game.id) == local_game

    def test_duplicate_game_raises(
        self, library: Library, local_game: Game
    ) -> None:
        """Adding the same game twice should raise DuplicateGameError."""
        library.add_game(local_game)
        library.collect_events()
        with pytest.raises(DuplicateGameError, match="already exists"):
            library.add_game(local_game)

    def test_add_any_store_game(
        self, library: Library, epic_game: Game
    ) -> None:
        """Any game from any store can be added to any library (unified library)."""
        library.add_game(epic_game)
        assert library.game_count == 1
        assert library.get_game(epic_game.id) == epic_game

    def test_add_emits_event(
        self, library: Library, local_game: Game
    ) -> None:
        """Adding a game should emit a GameAdded event."""
        library.add_game(local_game)
        events = library.collect_events()
        assert len(events) == 1
        assert events[0].title == "Test Game"  # type: ignore[attr-defined]  # type: ignore[attr-defined]


class TestLibraryRemoveGame:
    """Tests for removing games from a library."""

    def test_remove_existing(
        self, library: Library, local_game: Game
    ) -> None:
        """Removing an existing game should decrease game count."""
        library.add_game(local_game)
        library.collect_events()
        removed = library.remove_game(local_game.id)
        assert removed == local_game
        assert library.game_count == 0

    def test_remove_nonexistent_raises(self, library: Library) -> None:
        """Removing a non-existent game should raise GameNotFoundError."""
        fake_id = GameId.generate()
        with pytest.raises(GameNotFoundError, match="not found"):
            library.remove_game(fake_id)

    def test_remove_emits_event(
        self, library: Library, local_game: Game
    ) -> None:
        """Removing a game should emit a GameRemoved event."""
        library.add_game(local_game)
        library.collect_events()
        library.remove_game(local_game.id)
        events = library.collect_events()
        assert len(events) == 1
        assert events[0].title == "Test Game"  # type: ignore[attr-defined]


class TestLibraryFindByTitle:
    """Tests for finding games by title."""

    def test_find_exact_match(
        self, library: Library, local_game: Game
    ) -> None:
        """Should find games by exact title match."""
        library.add_game(local_game)
        results = library.find_by_title("Test Game")
        assert len(results) == 1

    def test_find_case_insensitive(
        self, library: Library, local_game: Game
    ) -> None:
        """Search should be case-insensitive."""
        library.add_game(local_game)
        results = library.find_by_title("test game")
        assert len(results) == 1

    def test_find_partial_match(
        self, library: Library, local_game: Game
    ) -> None:
        """Should find games by partial title match."""
        library.add_game(local_game)
        results = library.find_by_title("Test")
        assert len(results) == 1

    def test_find_no_match(
        self, library: Library, local_game: Game
    ) -> None:
        """Should return empty list for non-matching titles."""
        library.add_game(local_game)
        results = library.find_by_title("Nonexistent")
        assert results == []
