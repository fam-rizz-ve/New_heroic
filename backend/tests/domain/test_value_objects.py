"""Tests for domain value objects."""

import pytest

from app.core.domain.value_objects import (
    ExecutablePath,
    GameTitle,
    InstallPath,
)


class TestGameTitle:
    """Tests for the GameTitle value object."""

    def test_valid_title(self) -> None:
        """Should create a GameTitle with a valid non-empty string."""
        title = GameTitle("Cyberpunk 2077")
        assert title.value == "Cyberpunk 2077"

    def test_empty_title_raises(self) -> None:
        """Should raise ValueError for empty string."""
        with pytest.raises(ValueError, match="must not be empty"):
            GameTitle("")

    def test_whitespace_title_raises(self) -> None:
        """Should raise ValueError for whitespace-only string."""
        with pytest.raises(ValueError, match="must not be empty"):
            GameTitle("   ")

    def test_immutable(self) -> None:
        """GameTitle should be a frozen dataclass."""
        title = GameTitle("Test")
        with pytest.raises(AttributeError):
            title.value = "Changed"  # type: ignore[misc]


class TestInstallPath:
    """Tests for the InstallPath value object."""

    def test_valid_path(self) -> None:
        """Should create an InstallPath with a valid non-empty string."""
        path = InstallPath("/home/games/cyberpunk")
        assert path.value == "/home/games/cyberpunk"

    def test_empty_path_raises(self) -> None:
        """Should raise ValueError for empty string."""
        with pytest.raises(ValueError, match="must not be empty"):
            InstallPath("")

    def test_immutable(self) -> None:
        """InstallPath should be a frozen dataclass."""
        path = InstallPath("/game")
        with pytest.raises(AttributeError):
            path.value = "/hacked"  # type: ignore[misc]


class TestExecutablePath:
    """Tests for the ExecutablePath value object."""

    def test_valid_path(self) -> None:
        """Should create an ExecutablePath with a valid non-empty string."""
        path = ExecutablePath("/home/games/cyberpunk/bin/game")
        assert path.value == "/home/games/cyberpunk/bin/game"

    def test_empty_path_raises(self) -> None:
        """Should raise ValueError for empty string."""
        with pytest.raises(ValueError, match="must not be empty"):
            ExecutablePath("")

    def test_immutable(self) -> None:
        """ExecutablePath should be a frozen dataclass."""
        path = ExecutablePath("/game.exe")
        with pytest.raises(AttributeError):
            path.value = "/hacked.exe"  # type: ignore[misc]
