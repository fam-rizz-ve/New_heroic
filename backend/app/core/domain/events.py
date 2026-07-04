"""Domain events for the game library."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Base class for all domain events."""

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, kw_only=True)
class GameAdded(DomainEvent):
    """Emitted when a game is added to a library."""

    game_id: UUID
    title: str
    store: str


@dataclass(frozen=True, kw_only=True)
class GameRemoved(DomainEvent):
    """Emitted when a game is removed from a library."""

    game_id: UUID
    title: str


@dataclass(frozen=True, kw_only=True)
class GameInstallationStarted(DomainEvent):
    """Emitted when game installation begins."""

    game_id: UUID
    title: str


@dataclass(frozen=True, kw_only=True)
class GameInstalled(DomainEvent):
    """Emitted when a game finishes installing."""

    game_id: UUID
    title: str
    install_path: str


@dataclass(frozen=True, kw_only=True)
class GameUninstalled(DomainEvent):
    """Emitted when a game is uninstalled."""

    game_id: UUID
    title: str


@dataclass(frozen=True, kw_only=True)
class GameLaunched(DomainEvent):
    """Emitted when a game is launched."""

    game_id: UUID
    title: str


@dataclass(frozen=True, kw_only=True)
class GameClosed(DomainEvent):
    """Emitted when a running game is closed."""

    game_id: UUID
    title: str


@dataclass(frozen=True, kw_only=True)
class GameFavorited(DomainEvent):
    """Emitted when a game is favorited."""

    game_id: UUID
    title: str


@dataclass(frozen=True, kw_only=True)
class GameUnfavorited(DomainEvent):
    """Emitted when a game is unfavorited."""

    game_id: UUID
    title: str
