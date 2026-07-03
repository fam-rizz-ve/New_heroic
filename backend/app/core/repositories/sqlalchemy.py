"""SQLAlchemy implementations of repository interfaces.

These replace the in-memory repositories for production use.
They implement the same Protocol interfaces defined in
app.core.interfaces.repositories, but with SQLite (or other
RDBMS) persistence via SQLAlchemy.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.domain.game import Game as DomainGame
from app.core.domain.library import Library as DomainLibrary
from app.core.domain.value_objects import GameId, LibraryId
from app.models.game import GameModel
from app.models.library import LibraryModel


class SQLAlchemyGameRepository:
    """SQLAlchemy-backed implementation of GameRepository Protocol.

    All methods are synchronous to match the Protocol interface,
    which is consumed synchronously by LibraryUseCases.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, game: DomainGame) -> None:
        """Persist a game (create or update)."""
        existing = self._session.get(GameModel, str(game.id.value))
        if existing:
            existing.update_from_domain(game)
        else:
            self._session.add(GameModel.from_domain(game))
        self._session.commit()

    def get(self, game_id: GameId) -> DomainGame | None:
        """Get a game by its ID. Returns None if not found."""
        model = self._session.get(GameModel, str(game_id.value))
        if model is None:
            return None
        return model.to_domain()

    def delete(self, game_id: GameId) -> None:
        """Delete a game by its ID. Raises KeyError if not found."""
        model = self._session.get(GameModel, str(game_id.value))
        if model is None:
            raise KeyError(f"Game with id '{game_id.value}' not found")
        self._session.delete(model)
        self._session.commit()

    def list_all(self) -> list[DomainGame]:
        """List all games."""
        result = self._session.execute(select(GameModel))
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    def find_by_title(self, query: str) -> list[DomainGame]:
        """Find games whose title contains the query (case-insensitive)."""
        result = self._session.execute(
            select(GameModel).where(GameModel.title.ilike(f"%{query}%"))
        )
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    def count(self) -> int:
        """Return the total number of games."""
        result = self._session.execute(select(GameModel))
        return len(result.scalars().all())


class SQLAlchemyLibraryRepository:
    """SQLAlchemy-backed implementation of LibraryRepository Protocol.

    All methods are synchronous to match the Protocol interface,
    which is consumed synchronously by LibraryUseCases.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, library: DomainLibrary) -> None:
        """Persist a library (create or update)."""
        existing = self._session.get(
            LibraryModel, str(library.id.value)
        )
        if existing:
            existing.update_from_domain(library)
        else:
            self._session.add(LibraryModel.from_domain(library))
        self._session.commit()

    def _hydrate_games(self, library: DomainLibrary) -> DomainLibrary:
        """Attach all games from the games table to the library.

        The domain Library aggregate owns its games via the ``games`` dict,
        but the SQL schema stores games in a separate ``games`` table without
        a library FK (Heroic-style unified library). This helper loads all
        games and attaches them so that the domain object behaves correctly.
        """
        result = self._session.execute(select(GameModel))
        for model in result.scalars().all():
            game = model.to_domain()
            if game.id not in library.games:
                library.games[game.id] = game
        return library

    def get(self, library_id: LibraryId) -> DomainLibrary | None:
        """Get a library by its ID. Returns None if not found."""
        model = self._session.get(LibraryModel, str(library_id.value))
        if model is None:
            return None
        library = model.to_domain()
        return self._hydrate_games(library)

    def delete(self, library_id: LibraryId) -> None:
        """Delete a library by its ID. Raises KeyError if not found."""
        model = self._session.get(LibraryModel, str(library_id.value))
        if model is None:
            raise KeyError(
                f"Library with id '{library_id.value}' not found"
            )
        self._session.delete(model)
        self._session.commit()

    def list_all(self) -> list[DomainLibrary]:
        """List all libraries."""
        result = self._session.execute(select(LibraryModel))
        models = result.scalars().all()
        return [self._hydrate_games(m.to_domain()) for m in models]

    def count(self) -> int:
        """Return the total number of libraries."""
        result = self._session.execute(select(LibraryModel))
        return len(result.scalars().all())
