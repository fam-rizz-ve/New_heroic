"""Tests for in-memory repository implementations."""

import pytest

from app.core.domain.enums import RunnerType, StoreSource
from app.core.domain.game import Game
from app.core.domain.library import Library
from app.core.domain.value_objects import GameId, GameTitle, LibraryId
from app.core.repositories.in_memory import (
    InMemoryGameRepository,
    InMemoryLibraryRepository,
)


class TestInMemoryGameRepository:
    """Tests for the in-memory game repository."""

    @pytest.fixture
    def repo(self) -> InMemoryGameRepository:
        """Create a fresh repository fixture."""
        return InMemoryGameRepository()

    @pytest.fixture
    def game(self) -> Game:
        """Create a fresh game fixture."""
        return Game(
            id=GameId.generate(),
            title=GameTitle("Test Game"),
            store=StoreSource.LOCAL,
            runner=RunnerType.NATIVE,
        )

    def test_save_and_get(
        self, repo: InMemoryGameRepository, game: Game
    ) -> None:
        """Saved game should be retrievable by ID."""
        repo.save(game)
        retrieved = repo.get(game.id)
        assert retrieved is not None
        assert retrieved.title.value == "Test Game"

    def test_get_nonexistent(self, repo: InMemoryGameRepository) -> None:
        """Getting a non-existent game should return None."""
        assert repo.get(GameId.generate()) is None

    def test_delete_existing(
        self, repo: InMemoryGameRepository, game: Game
    ) -> None:
        """Deleted game should no longer be retrievable."""
        repo.save(game)
        repo.delete(game.id)
        assert repo.get(game.id) is None

    def test_delete_nonexistent_raises(
        self, repo: InMemoryGameRepository
    ) -> None:
        """Deleting a non-existent game should raise KeyError."""
        with pytest.raises(KeyError, match="not found"):
            repo.delete(GameId.generate())

    def test_count(self, repo: InMemoryGameRepository, game: Game) -> None:
        """Count should reflect number of saved games."""
        assert repo.count() == 0
        repo.save(game)
        assert repo.count() == 1

    def test_list_all(
        self, repo: InMemoryGameRepository, game: Game
    ) -> None:
        """List all should return all saved games."""
        repo.save(game)
        games = repo.list_all()
        assert len(games) == 1
        assert games[0].id == game.id

    def test_find_by_title(
        self, repo: InMemoryGameRepository, game: Game
    ) -> None:
        """Find by title should return matching games."""
        repo.save(game)
        results = repo.find_by_title("Test")
        assert len(results) == 1

    def test_find_by_title_no_match(
        self, repo: InMemoryGameRepository, game: Game
    ) -> None:
        """Find by title with no match should return empty list."""
        repo.save(game)
        results = repo.find_by_title("Nonexistent")
        assert results == []

    def test_save_updates_existing(
        self, repo: InMemoryGameRepository, game: Game
    ) -> None:
        """Saving an existing game should update it."""
        repo.save(game)
        game.description = "Updated description"
        repo.save(game)
        retrieved = repo.get(game.id)
        assert retrieved is not None
        assert retrieved.description == "Updated description"

    def test_count_after_delete(
        self, repo: InMemoryGameRepository, game: Game
    ) -> None:
        """Count should decrease after deleting a game."""
        repo.save(game)
        repo.delete(game.id)
        assert repo.count() == 0


class TestInMemoryLibraryRepository:
    """Tests for the in-memory library repository."""

    @pytest.fixture
    def repo(self) -> InMemoryLibraryRepository:
        """Create a fresh repository fixture."""
        return InMemoryLibraryRepository()

    @pytest.fixture
    def library(self) -> Library:
        """Create a fresh library fixture."""
        return Library(
            id=LibraryId.generate(),
            name="Test Library",
            store_source=StoreSource.LOCAL,
        )

    def test_save_and_get(
        self, repo: InMemoryLibraryRepository, library: Library
    ) -> None:
        """Saved library should be retrievable by ID."""
        repo.save(library)
        retrieved = repo.get(library.id)
        assert retrieved is not None
        assert retrieved.name == "Test Library"

    def test_get_nonexistent(
        self, repo: InMemoryLibraryRepository
    ) -> None:
        """Getting a non-existent library should return None."""
        assert repo.get(LibraryId.generate()) is None

    def test_count(
        self, repo: InMemoryLibraryRepository, library: Library
    ) -> None:
        """Count should reflect number of saved libraries."""
        assert repo.count() == 0
        repo.save(library)
        assert repo.count() == 1

    def test_list_all(
        self, repo: InMemoryLibraryRepository, library: Library
    ) -> None:
        """List all should return all saved libraries."""
        repo.save(library)
        libraries = repo.list_all()
        assert len(libraries) == 1
        assert libraries[0].id == library.id

    def test_delete_existing(
        self, repo: InMemoryLibraryRepository, library: Library
    ) -> None:
        """Deleted library should no longer be retrievable."""
        repo.save(library)
        repo.delete(library.id)
        assert repo.get(library.id) is None

    def test_delete_nonexistent_raises(
        self, repo: InMemoryLibraryRepository
    ) -> None:
        """Deleting a non-existent library should raise KeyError."""
        with pytest.raises(KeyError, match="not found"):
            repo.delete(LibraryId.generate())

    def test_count_after_delete(
        self, repo: InMemoryLibraryRepository, library: Library
    ) -> None:
        """Count should decrease after deleting a library."""
        repo.save(library)
        repo.delete(library.id)
        assert repo.count() == 0
