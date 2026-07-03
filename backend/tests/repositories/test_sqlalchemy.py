"""Tests for SQLAlchemy repository implementations.

Mirrors the test_in_memory.py patterns exactly to ensure
equivalent behavior from the SQLAlchemy-backed implementations.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.core.domain.enums import RunnerType, StoreSource
from app.core.domain.game import Game
from app.core.domain.library import Library
from app.core.domain.value_objects import GameId, GameTitle, LibraryId
from app.core.repositories.sqlalchemy import (
    SQLAlchemyGameRepository,
    SQLAlchemyLibraryRepository,
)


@pytest.fixture
def session() -> Iterator[Session]:
    """Create a clean in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(engine)
    s = session_factory()
    yield s
    s.close()
    engine.dispose()


@pytest.fixture
def game_repo(session: Session) -> SQLAlchemyGameRepository:
    """Create a fresh SQLAlchemy game repository."""
    return SQLAlchemyGameRepository(session)


@pytest.fixture
def library_repo(session: Session) -> SQLAlchemyLibraryRepository:
    """Create a fresh SQLAlchemy library repository."""
    return SQLAlchemyLibraryRepository(session)


@pytest.fixture
def game() -> Game:
    """Create a fresh domain game fixture."""
    return Game(
        id=GameId.generate(),
        title=GameTitle("Test Game"),
        store=StoreSource.LOCAL,
        runner=RunnerType.NATIVE,
    )


@pytest.fixture
def library() -> Library:
    """Create a fresh domain library fixture."""
    return Library(
        id=LibraryId.generate(),
        name="Test Library",
        store_source=StoreSource.LOCAL,
    )


class TestSQLAlchemyGameRepository:
    """Tests for SQLAlchemy game repository."""

    def test_save_and_get(
        self, game_repo: SQLAlchemyGameRepository, game: Game
    ) -> None:
        """Saved game should be retrievable by ID."""
        game_repo.save(game)
        retrieved = game_repo.get(game.id)
        assert retrieved is not None
        assert retrieved.title.value == "Test Game"

    def test_get_nonexistent(
        self, game_repo: SQLAlchemyGameRepository
    ) -> None:
        """Getting a non-existent game should return None."""
        assert game_repo.get(GameId.generate()) is None

    def test_delete_existing(
        self, game_repo: SQLAlchemyGameRepository, game: Game
    ) -> None:
        """Deleted game should no longer be retrievable."""
        game_repo.save(game)
        game_repo.delete(game.id)
        assert game_repo.get(game.id) is None

    def test_delete_nonexistent_raises(
        self, game_repo: SQLAlchemyGameRepository
    ) -> None:
        """Deleting a non-existent game should raise KeyError."""
        with pytest.raises(KeyError, match="not found"):
            game_repo.delete(GameId.generate())

    def test_count(
        self, game_repo: SQLAlchemyGameRepository, game: Game
    ) -> None:
        """Count should reflect number of saved games."""
        assert game_repo.count() == 0
        game_repo.save(game)
        assert game_repo.count() == 1

    def test_list_all(
        self, game_repo: SQLAlchemyGameRepository, game: Game
    ) -> None:
        """List all should return all saved games."""
        game_repo.save(game)
        games = game_repo.list_all()
        assert len(games) == 1
        assert games[0].id == game.id

    def test_find_by_title(
        self, game_repo: SQLAlchemyGameRepository, game: Game
    ) -> None:
        """Find by title should return matching games."""
        game_repo.save(game)
        results = game_repo.find_by_title("Test")
        assert len(results) == 1

    def test_find_by_title_no_match(
        self, game_repo: SQLAlchemyGameRepository, game: Game
    ) -> None:
        """Find by title with no match should return empty list."""
        game_repo.save(game)
        results = game_repo.find_by_title("Nonexistent")
        assert results == []

    def test_save_updates_existing(
        self, game_repo: SQLAlchemyGameRepository, game: Game
    ) -> None:
        """Saving an existing game should update it."""
        game_repo.save(game)
        game.description = "Updated description"
        game_repo.save(game)
        retrieved = game_repo.get(game.id)
        assert retrieved is not None
        assert retrieved.description == "Updated description"

    def test_count_after_delete(
        self, game_repo: SQLAlchemyGameRepository, game: Game
    ) -> None:
        """Count should decrease after deleting a game."""
        game_repo.save(game)
        game_repo.delete(game.id)
        assert game_repo.count() == 0


class TestSQLAlchemyLibraryRepository:
    """Tests for SQLAlchemy library repository."""

    def test_save_and_get(
        self, library_repo: SQLAlchemyLibraryRepository, library: Library
    ) -> None:
        """Saved library should be retrievable by ID."""
        library_repo.save(library)
        retrieved = library_repo.get(library.id)
        assert retrieved is not None
        assert retrieved.name == "Test Library"

    def test_get_nonexistent(
        self, library_repo: SQLAlchemyLibraryRepository
    ) -> None:
        """Getting a non-existent library should return None."""
        assert library_repo.get(LibraryId.generate()) is None

    def test_count(
        self, library_repo: SQLAlchemyLibraryRepository, library: Library
    ) -> None:
        """Count should reflect number of saved libraries."""
        assert library_repo.count() == 0
        library_repo.save(library)
        assert library_repo.count() == 1

    def test_list_all(
        self, library_repo: SQLAlchemyLibraryRepository, library: Library
    ) -> None:
        """List all should return all saved libraries."""
        library_repo.save(library)
        libraries = library_repo.list_all()
        assert len(libraries) == 1
        assert libraries[0].id == library.id

    def test_delete_existing(
        self, library_repo: SQLAlchemyLibraryRepository, library: Library
    ) -> None:
        """Deleted library should no longer be retrievable."""
        library_repo.save(library)
        library_repo.delete(library.id)
        assert library_repo.get(library.id) is None

    def test_delete_nonexistent_raises(
        self, library_repo: SQLAlchemyLibraryRepository
    ) -> None:
        """Deleting a non-existent library should raise KeyError."""
        with pytest.raises(KeyError, match="not found"):
            library_repo.delete(LibraryId.generate())

    def test_count_after_delete(
        self, library_repo: SQLAlchemyLibraryRepository, library: Library
    ) -> None:
        """Count should decrease after deleting a library."""
        library_repo.save(library)
        library_repo.delete(library.id)
        assert library_repo.count() == 0
