"""SQLAlchemy model for Game."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.domain.enums import GameStatus, RunnerType, StoreSource
from app.core.domain.game import Game as DomainGame
from app.core.domain.value_objects import (
    ExecutablePath,
    GameId,
    GameTitle,
    InstallPath,
)


class GameModel(Base):
    """SQLAlchemy model matching the Game domain entity."""

    __tablename__ = "games"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    store: Mapped[str] = mapped_column(String(50), nullable=False)
    runner: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default=GameStatus.NOT_INSTALLED.value, nullable=False
    )
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    cover_art_url: Mapped[str] = mapped_column(Text, default="", nullable=False)
    store_id: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    install_path: Mapped[str | None] = mapped_column(
        String(1024), nullable=True
    )
    executable_path: Mapped[str | None] = mapped_column(
        String(1024), nullable=True
    )
    last_played: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    total_play_time_seconds: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    is_favorite: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def to_domain(self) -> DomainGame:
        """Convert ORM model to domain Game."""
        return DomainGame(
            id=GameId.from_str(self.id),
            title=GameTitle(self.title),
            store=StoreSource(self.store),
            runner=RunnerType(self.runner),
            status=GameStatus(self.status),
            description=self.description,
            cover_art_url=self.cover_art_url,
            store_id=self.store_id,
            install_path=InstallPath(self.install_path)
            if self.install_path
            else None,
            executable_path=ExecutablePath(self.executable_path)
            if self.executable_path
            else None,
            last_played=self.last_played,
            total_play_time_seconds=self.total_play_time_seconds,
            is_favorite=self.is_favorite,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, game: DomainGame) -> GameModel:
        """Create ORM model from domain Game."""
        return cls(
            id=str(game.id.value),
            title=game.title.value,
            store=game.store.value,
            runner=game.runner.value,
            status=game.status.value,
            description=game.description,
            cover_art_url=game.cover_art_url,
            store_id=game.store_id,
            install_path=game.install_path.value
            if game.install_path
            else None,
            executable_path=game.executable_path.value
            if game.executable_path
            else None,
            last_played=game.last_played,
            total_play_time_seconds=game.total_play_time_seconds,
            is_favorite=game.is_favorite,
            created_at=game.created_at,
            updated_at=game.updated_at,
        )

    def update_from_domain(self, game: DomainGame) -> None:
        """Update ORM model fields from domain Game."""
        self.title = game.title.value
        self.store = game.store.value
        self.runner = game.runner.value
        self.status = game.status.value
        self.description = game.description
        self.cover_art_url = game.cover_art_url
        self.store_id = game.store_id
        self.install_path = (
            game.install_path.value if game.install_path else None
        )
        self.executable_path = (
            game.executable_path.value if game.executable_path else None
        )
        self.last_played = game.last_played
        self.total_play_time_seconds = game.total_play_time_seconds
        self.is_favorite = game.is_favorite
        self.updated_at = game.updated_at
