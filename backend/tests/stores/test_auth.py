"""Tests for store OAuth auth URL generation."""

from __future__ import annotations

import pytest

from app.stores.epic import EpicStore
from app.stores.gog import GOGStore


class TestEpicAuth:
    """Tests for EpicStore OAuth methods."""

    @pytest.fixture
    def store(self) -> EpicStore:
        """Create an EpicStore instance."""
        return EpicStore()

    @pytest.mark.asyncio
    async def test_get_auth_url(self, store: EpicStore) -> None:
        """Auth URL should point to the Epic Games login page."""
        url = await store.get_auth_url()
        assert "epicgames.com" in url
        assert "/id/login" in url

    @pytest.mark.asyncio
    async def test_get_auth_instructions(self, store: EpicStore) -> None:
        """Instructions should be a non-empty string."""
        instructions = await store.get_auth_instructions()
        assert isinstance(instructions, str)
        assert len(instructions) > 0
        assert "Epic Games" in instructions or "epic" in instructions.lower()


class TestGOGAuth:
    """Tests for GOGStore OAuth methods."""

    @pytest.fixture
    def store(self) -> GOGStore:
        """Create a GOGStore instance."""
        return GOGStore()

    @pytest.mark.asyncio
    async def test_get_auth_url(self, store: GOGStore) -> None:
        """Auth URL should point to the GOG OAuth page."""
        url = await store.get_auth_url()
        assert "auth.gog.com" in url
        assert "client_id=46899977096215655" in url
        assert "response_type=code" in url

    @pytest.mark.asyncio
    async def test_get_auth_instructions(self, store: GOGStore) -> None:
        """Instructions should be a non-empty string."""
        instructions = await store.get_auth_instructions()
        assert isinstance(instructions, str)
        assert len(instructions) > 0
        assert "GOG" in instructions
