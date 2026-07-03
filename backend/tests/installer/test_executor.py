"""Tests for installer executor."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from app.installer.executor import InstallExecutor
from app.installer.models import InstallerManifest, InstallerStep


class TestInstallExecutor:
    """Tests for the sequential step executor."""

    @pytest.mark.asyncio
    async def test_execute_mkdir_step(self) -> None:
        """Execute a mkdir step creates the directory."""
        manifest = InstallerManifest(
            name="Test",
            game_slug="test",
            version="1.0",
            steps=[
                InstallerStep(action="mkdir", config={"path": "subdir"}),
            ],
        )
        with TemporaryDirectory() as tmpdir:
            executor = InstallExecutor(manifest, tmpdir)
            await executor.execute()
            assert (Path(tmpdir) / "subdir").exists()

    @pytest.mark.asyncio
    async def test_execute_chmodx_step(self) -> None:
        """Execute a chmodx step makes a file executable."""
        manifest = InstallerManifest(
            name="Test",
            game_slug="test",
            version="1.0",
            steps=[
                InstallerStep(action="chmodx", config={"value": "test.sh"}),
            ],
        )
        with TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test.sh"
            test_file.write_text("#!/bin/sh\necho hello")
            test_file.chmod(0o644)

            executor = InstallExecutor(manifest, tmpdir)
            await executor.execute()
            assert test_file.stat().st_mode & 0o111  # executable bit set

    @pytest.mark.asyncio
    async def test_cancel_installation(self) -> None:
        """Cancelling an installation stops after current step."""
        manifest = InstallerManifest(
            name="Test",
            game_slug="test",
            version="1.0",
            steps=[
                InstallerStep(action="mkdir", config={"path": "dir1"}),
                InstallerStep(action="mkdir", config={"path": "dir2"}),
            ],
        )
        with TemporaryDirectory() as tmpdir:
            progress_updates: list[tuple[int, str]] = []

            def on_progress(step: int, total: int, action: str, desc: str) -> None:
                progress_updates.append((step, action))
                if step == 0:
                    executor.cancel()

            executor = InstallExecutor(manifest, tmpdir)
            await executor.execute(on_progress=on_progress)

            # Only first step should have executed
            dir1 = Path(tmpdir) / "dir1"
            dir2 = Path(tmpdir) / "dir2"
            assert dir1.exists()
            assert not dir2.exists()
