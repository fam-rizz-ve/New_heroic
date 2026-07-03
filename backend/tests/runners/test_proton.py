"""Tests for ProtonRunner."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.runners.proton import ProtonRunner


@pytest.fixture
def runner() -> ProtonRunner:
    """Create a ProtonRunner instance for testing."""
    return ProtonRunner()


@pytest.mark.asyncio
async def test_detect_not_installed(runner: ProtonRunner) -> None:
    """Test detection when Proton is not installed."""
    # Mock the filesystem to simulate no Proton installations
    with (
        patch("os.path.isdir", return_value=False),
        patch("os.listdir", return_value=[]),
    ):
        info = await runner.detect()
        assert info.is_installed is False


@pytest.mark.asyncio
async def test_get_settings(runner: ProtonRunner) -> None:
    """Test get_settings returns correct defaults."""
    settings = await runner.get_settings()
    assert settings["name"] == "proton"
