"""Tests for the Game aggregate."""

import pytest

from app.core.domain.enums import GameStatus, RunnerType, StoreSource
from app.core.domain.game import Game, InvalidStateTransitionError
from app.core.domain.value_objects import GameId, GameTitle


@pytest.fixture
def game() -> Game:
    """Create a fresh Game fixture for testing."""
    return Game(
        id=GameId.generate(),
        title=GameTitle("Test Game"),
        store=StoreSource.LOCAL,
        runner=RunnerType.NATIVE,
    )


class TestGameInitialState:
    """Tests for the initial state of a Game."""

    def test_starts_not_installed(self, game: Game) -> None:
        """A new game should start as NOT_INSTALLED."""
        assert game.status == GameStatus.NOT_INSTALLED

    def test_no_install_path(self, game: Game) -> None:
        """A new game should not have an install path."""
        assert game.install_path is None

    def test_no_events_initially(self, game: Game) -> None:
        """A new game should have no pending events."""
        assert game.collect_events() == []


class TestGameInstallation:
    """Tests for game installation flows."""

    def test_start_installation(self, game: Game) -> None:
        """Starting installation should set status to INSTALLING."""
        game.start_installation()
        assert game.status == GameStatus.INSTALLING
        events = game.collect_events()
        assert len(events) == 1
        assert events[0].title == "Test Game"  # type: ignore[attr-defined]

    def test_cannot_install_when_already_installed(self, game: Game) -> None:
        """Should raise when trying to install an already installed game."""
        game.start_installation()
        game.complete_installation("/path", "/exe")
        game.collect_events()
        with pytest.raises(
            InvalidStateTransitionError, match="already installed"
        ):
            game.start_installation()

    def test_cannot_install_when_already_installing(self, game: Game) -> None:
        """Should raise when trying to install while already installing."""
        game.start_installation()
        game.collect_events()
        with pytest.raises(
            InvalidStateTransitionError, match="already in progress"
        ):
            game.start_installation()

    def test_complete_installation(self, game: Game) -> None:
        """Completing installation should set correct state and paths."""
        game.start_installation()
        game.collect_events()
        game.complete_installation("/path/to/game", "/path/to/game/exe")
        assert game.status == GameStatus.INSTALLED
        assert game.install_path is not None
        assert game.install_path.value == "/path/to/game"
        assert game.executable_path is not None
        assert game.executable_path.value == "/path/to/game/exe"
        events = game.collect_events()
        assert len(events) == 1
        assert events[0].install_path == "/path/to/game"  # type: ignore[attr-defined]

    def test_cannot_complete_if_not_installing(self, game: Game) -> None:
        """Should raise when completing installation that was never started."""
        with pytest.raises(
            InvalidStateTransitionError, match="not currently installing"
        ):
            game.complete_installation("/path", "/exe")


class TestGameUninstall:
    """Tests for game uninstallation."""

    def test_uninstall_installed_game(self, game: Game) -> None:
        """Uninstalling should reset state and clear paths."""
        game.start_installation()
        game.complete_installation("/path", "/exe")
        game.collect_events()
        game.uninstall()
        assert game.status == GameStatus.NOT_INSTALLED
        assert game.install_path is None
        assert game.executable_path is None

    def test_cannot_uninstall_not_installed(self, game: Game) -> None:
        """Should raise when trying to uninstall a game that was never installed."""
        with pytest.raises(
            InvalidStateTransitionError, match="not installed"
        ):
            game.uninstall()

    def test_cannot_uninstall_running_game(self, game: Game) -> None:
        """Should raise when trying to uninstall a currently running game."""
        game.start_installation()
        game.complete_installation("/path", "/exe")
        game.launch()
        game.collect_events()
        with pytest.raises(
            InvalidStateTransitionError, match="currently running"
        ):
            game.uninstall()


class TestGameLaunchAndClose:
    """Tests for game launch and close lifecycle."""

    def test_launch_installed_game(self, game: Game) -> None:
        """Launching an installed game should set status to RUNNING."""
        game.start_installation()
        game.complete_installation("/path", "/exe")
        game.collect_events()
        game.launch()
        assert game.status == GameStatus.RUNNING
        assert game.last_played is not None

    def test_cannot_launch_not_installed(self, game: Game) -> None:
        """Should raise when trying to launch a game that is not installed."""
        with pytest.raises(
            InvalidStateTransitionError, match="not installed"
        ):
            game.launch()

    def test_close_running_game(self, game: Game) -> None:
        """Closing a running game should return to INSTALLED status."""
        game.start_installation()
        game.complete_installation("/path", "/exe")
        game.launch()
        game.collect_events()
        game.close()
        assert game.status == GameStatus.INSTALLED

    def test_cannot_close_not_running(self, game: Game) -> None:
        """Should raise when trying to close a game that is not running."""
        with pytest.raises(
            InvalidStateTransitionError, match="not running"
        ):
            game.close()


class TestGameError:
    """Tests for game error state."""

    def test_mark_error_from_any_state(self, game: Game) -> None:
        """Should be able to mark error from NOT_INSTALLED state."""
        game.mark_error()
        assert game.status == GameStatus.ERROR

    def test_mark_error_from_installing(self, game: Game) -> None:
        """Should be able to mark error from INSTALLING state."""
        game.start_installation()
        game.mark_error()
        assert game.status == GameStatus.ERROR


class TestGameFavorites:
    """Tests for game favorite toggling."""

    def test_starts_not_favorite(self, game: Game) -> None:
        """A new game should not be favorited by default."""
        assert game.is_favorite is False

    def test_toggle_favorite(self, game: Game) -> None:
        """Toggling favorite should set is_favorite to True."""
        game.toggle_favorite()
        assert game.is_favorite is True

    def test_toggle_favorite_twice(self, game: Game) -> None:
        """Toggling favorite twice should return to False."""
        game.toggle_favorite()
        game.toggle_favorite()
        assert game.is_favorite is False

    def test_toggle_favorite_updates_timestamp(self, game: Game) -> None:
        """Toggling favorite should update the updated_at timestamp."""
        old = game.updated_at
        game.toggle_favorite()
        assert game.updated_at >= old
