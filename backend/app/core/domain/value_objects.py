"""Value objects for the game library domain."""

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class GameId:
    """Unique identifier for a game."""

    value: UUID

    @classmethod
    def generate(cls) -> "GameId":
        """Create a new unique game ID."""
        return cls(value=uuid4())

    @classmethod
    def from_str(cls, value: str) -> "GameId":
        """Parse a GameId from a string."""
        return cls(value=UUID(value))


@dataclass(frozen=True)
class LibraryId:
    """Unique identifier for a library."""

    value: UUID

    @classmethod
    def generate(cls) -> "LibraryId":
        """Create a new unique library ID."""
        return cls(value=uuid4())

    @classmethod
    def from_str(cls, value: str) -> "LibraryId":
        """Parse a LibraryId from a string."""
        return cls(value=UUID(value))


@dataclass(frozen=True)
class GameTitle:
    """A game's display title. Must not be empty."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("Game title must not be empty")


@dataclass(frozen=True)
class InstallPath:
    """Filesystem path where a game is installed."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("Install path must not be empty")


@dataclass(frozen=True)
class ExecutablePath:
    """Filesystem path to a game's executable."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("Executable path must not be empty")
