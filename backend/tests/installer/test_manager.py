"""Tests for InstallerManager."""

from tempfile import TemporaryDirectory

import pytest

from app.installer.manager import InstallerManager


class TestInstallerManager:
    """Tests for the installer manager."""

    VALID_YAML = """
name: Test Game
game_slug: test-game
version: "1.0"
runner: wine

installer:
  - mkdir:
      description: Create game directory
      path: $GAMEDIR
"""

    def test_parse_installer(self) -> None:
        """Parse a valid YAML installer via the manager."""
        manager = InstallerManager()
        manifest = manager.parse_installer(self.VALID_YAML)
        assert manifest.name == "Test Game"
        assert manifest.game_slug == "test-game"

    def test_list_available_no_directory(self) -> None:
        """List available installers when no directory is set."""
        manager = InstallerManager()
        assert manager.list_available_installers() == []

    @pytest.mark.asyncio
    async def test_run_installer_and_cancel(self) -> None:
        """Run and cancel an installation via the manager."""
        manager = InstallerManager()
        manifest = manager.parse_installer(self.VALID_YAML)

        with TemporaryDirectory() as tmpdir:
            # Run installer and cancel it
            async def run_and_cancel() -> None:
                await manager.run_installer(manifest, tmpdir)
                manager.cancel_installation(manifest.game_slug)

            await run_and_cancel()

    def test_cancel_nonexistent(self) -> None:
        """Cancelling a non-existent installation returns False."""
        manager = InstallerManager()
        assert manager.cancel_installation("nonexistent") is False
