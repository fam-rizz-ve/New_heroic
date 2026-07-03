"""Tests for NativeRunner."""

from __future__ import annotations

import pytest

from app.runners.native import NativeRunner


@pytest.fixture
def runner() -> NativeRunner:
    """Create a NativeRunner instance for testing."""
    return NativeRunner()


@pytest.mark.asyncio
async def test_detect(runner: NativeRunner) -> None:
    """Test detection of native runner."""
    info = await runner.detect()
    assert info.name == "native"
    assert info.is_installed is True


@pytest.mark.asyncio
async def test_get_settings(runner: NativeRunner) -> None:
    """Test get_settings returns correct defaults."""
    settings = await runner.get_settings()
    assert settings["name"] == "native"
