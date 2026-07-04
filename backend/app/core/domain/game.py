"""Game aggregate root."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from app.core.domain.enums import GameStatus, RunnerType, StoreSource
from app.core.domain.events import (
    DomainEvent,
    GameClosed,
    GameFavorited,
    GameInstallationStarted,
    GameInstalled,
    GameLaunched,
    GameUnfavorited,
    GameUninstalled,
)
from app.core.domain.value_objects import ExecutablePath, GameId, GameTitle, InstallPath


class InvalidStateTransitionError(Exception):
    """Raised when a game status transition is invalid."""


@dataclass
class Game:
    """A game in the library. Aggregate root.

    Invariants:
    - Status transitions follow a valid state machine
    - Cannot launch if not installed
    - Cannot uninstall if not installed
    - Cannot install if already installed
    """

    id: GameId
    title: GameTitle
    store: StoreSource
    runner: RunnerType
    status: GameStatus = GameStatus.NOT_INSTALLED
    description: str = ""
    cover_art_url: str = ""
    install_path: InstallPath | None = None
    executable_path: ExecutablePath | None = None
    last_played: datetime | None = None
    total_play_time_seconds: int = 0
    is_favorite: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    _events: list[DomainEvent] = field(default_factory=list, init=False, repr=False)

    def collect_events(self) -> list[DomainEvent]:
        """Collect and clear pending domain events."""
        events = self._events
        self._events = []
        return events

    def start_installation(self) -> None:
        """Begin installing the game."""
        if self.status == GameStatus.INSTALLED:
            raise InvalidStateTransitionError(
                f"Cannot install game '{self.title.value}': already installed"
            )
        if self.status == GameStatus.INSTALLING:
            raise InvalidStateTransitionError(
                f"Cannot install game '{self.title.value}': installation already in progress"
            )
        if self.status == GameStatus.RUNNING:
            raise InvalidStateTransitionError(
                f"Cannot install game '{self.title.value}': game is currently running"
            )
        self.status = GameStatus.INSTALLING
        self.updated_at = datetime.now(UTC)
        self._events.append(
            GameInstallationStarted(
                event_id=uuid4(),
                game_id=self.id.value,
                title=self.title.value,
            )
        )

    def complete_installation(self, install_path: str, executable_path: str) -> None:
        """Mark installation as complete."""
        if self.status != GameStatus.INSTALLING:
            raise InvalidStateTransitionError(
                f"Cannot complete installation for game '{self.title.value}': "
                f"not currently installing (status: {self.status.value})"
            )
        self.status = GameStatus.INSTALLED
        self.install_path = InstallPath(install_path)
        self.executable_path = ExecutablePath(executable_path)
        self.updated_at = datetime.now(UTC)
        self._events.append(
            GameInstalled(
                event_id=uuid4(),
                game_id=self.id.value,
                title=self.title.value,
                install_path=install_path,
            )
        )

    def uninstall(self) -> None:
        """Uninstall the game."""
        if self.status == GameStatus.NOT_INSTALLED:
            raise InvalidStateTransitionError(
                f"Cannot uninstall game '{self.title.value}': not installed"
            )
        if self.status == GameStatus.INSTALLING:
            raise InvalidStateTransitionError(
                f"Cannot uninstall game '{self.title.value}': installation in progress"
            )
        if self.status == GameStatus.RUNNING:
            raise InvalidStateTransitionError(
                f"Cannot uninstall game '{self.title.value}': game is currently running"
            )
        self.status = GameStatus.NOT_INSTALLED
        self.install_path = None
        self.executable_path = None
        self.updated_at = datetime.now(UTC)
        self._events.append(
            GameUninstalled(
                event_id=uuid4(),
                game_id=self.id.value,
                title=self.title.value,
            )
        )

    def launch(self) -> None:
        """Launch the game."""
        if self.status != GameStatus.INSTALLED:
            raise InvalidStateTransitionError(
                f"Cannot launch game '{self.title.value}': not installed "
                f"(status: {self.status.value})"
            )
        self.status = GameStatus.RUNNING
        self.last_played = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)
        self._events.append(
            GameLaunched(
                event_id=uuid4(),
                game_id=self.id.value,
                title=self.title.value,
            )
        )

    def close(self) -> None:
        """Close a running game."""
        if self.status != GameStatus.RUNNING:
            raise InvalidStateTransitionError(
                f"Cannot close game '{self.title.value}': not running "
                f"(status: {self.status.value})"
            )
        self.status = GameStatus.INSTALLED
        self.updated_at = datetime.now(UTC)
        self._events.append(
            GameClosed(
                event_id=uuid4(),
                game_id=self.id.value,
                title=self.title.value,
            )
        )

    def set_cover_art(self, url: str) -> None:
        """Update the game's cover art URL."""
        self.cover_art_url = url
        self.updated_at = datetime.now(UTC)

    def toggle_favorite(self) -> None:
        """Toggle the favorite status of the game."""
        self.is_favorite = not self.is_favorite
        self.updated_at = datetime.now(UTC)
        if self.is_favorite:
            self._events.append(
                GameFavorited(
                    event_id=uuid4(),
                    game_id=self.id.value,
                    title=self.title.value,
                )
            )
        else:
            self._events.append(
                GameUnfavorited(
                    event_id=uuid4(),
                    game_id=self.id.value,
                    title=self.title.value,
                )
            )

    def mark_error(self) -> None:
        """Mark the game as being in an error state."""
        self.status = GameStatus.ERROR
        self.updated_at = datetime.now(UTC)
