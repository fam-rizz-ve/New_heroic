"""Tests for WineRunner."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from app.runners.wine import WineRunner


@pytest.fixture
def runner() -> WineRunner:
    """Create a WineRunner instance for testing."""
    return WineRunner()


@pytest.mark.asyncio
async def test_detect_not_installed(runner: WineRunner) -> None:
    """Test detection when Wine is not installed."""
    # Mock which to fail for both wine64 and wine
    original_exec = asyncio.create_subprocess_exec

    async def mock_exec(*args: Any, **kwargs: Any) -> Any:
        if args[0] == "which":
            mock_proc = AsyncMock()
            mock_proc.returncode = 1
            mock_proc.communicate = AsyncMock(return_value=(b"", b""))
            return mock_proc
        return await original_exec(*args, **kwargs)

    with patch("asyncio.create_subprocess_exec", side_effect=mock_exec):
        info = await runner.detect()
        assert info.is_installed is False
        assert info.path is None


@pytest.mark.asyncio
async def test_run_game_not_installed(runner: WineRunner) -> None:
    """Test run raises when Wine not detected."""
    with pytest.raises(RuntimeError, match="not installed"):
        await runner.run_game("/fake/game.exe")


@pytest.mark.asyncio
async def test_get_settings_defaults(runner: WineRunner) -> None:
    """Test get_settings returns correct defaults."""
    settings = await runner.get_settings()
    assert settings["name"] == "wine"
