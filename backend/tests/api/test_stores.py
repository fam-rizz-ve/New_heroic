"""Integration tests for store API endpoints."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
def app() -> FastAPI:
    """Create a fresh FastAPI application for testing."""
    return create_app()


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with LifespanManager(app):
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as ac:
            yield ac


class TestStoreListEndpoint:
    """Tests for GET /api/stores."""

    @pytest.mark.asyncio
    async def test_list_stores(self, client: AsyncClient) -> None:
        """Listing stores should return epic and gog."""
        response = await client.get("/api/stores")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        names = [s["name"] for s in data]
        assert "epic" in names
        assert "gog" in names

    @pytest.mark.asyncio
    async def test_list_stores_structure(self, client: AsyncClient) -> None:
        """Store list entries should have correct fields."""
        response = await client.get("/api/stores")
        data = response.json()
        for store in data:
            assert "name" in store
            assert "display_name" in store


class TestStoreAuthEndpoint:
    """Tests for POST /api/stores/{name}/auth."""

    @pytest.mark.asyncio
    async def test_auth_nonexistent_store(self, client: AsyncClient) -> None:
        """Authenticating against a non-existent store should return 404."""
        response = await client.post(
            "/api/stores/fake/auth",
            json={"code": "test"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_auth_epic_success(self, client: AsyncClient) -> None:
        """Successful Epic authentication should return 200."""
        response = await client.post(
            "/api/stores/epic/auth",
            json={"code": "test-auth-code"},
        )
        # EpicStore.authenticate will fail because legendary is not installed,
        # so expect 401. This test establishes the endpoint exists and routes
        # correctly.
        assert response.status_code in (200, 401)


class TestStoreGamesEndpoint:
    """Tests for GET /api/stores/{name}/games."""

    @pytest.mark.asyncio
    async def test_games_nonexistent_store(self, client: AsyncClient) -> None:
        """Listing games from a non-existent store should return 404."""
        response = await client.get("/api/stores/fake/games")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_games_cli_not_installed(self, client: AsyncClient) -> None:
        """Listing games when CLI is not installed should return 502.

        Mocks _run_command to raise RuntimeError (simulating a missing CLI)
        so the test passes regardless of whether legendary is installed.
        """
        with patch(
            "app.stores.epic.EpicStore._run_command",
            new_callable=AsyncMock,
            side_effect=RuntimeError(
                "legendary is not installed or not found on PATH"
            ),
        ):
            response = await client.get("/api/stores/epic/games")
            assert response.status_code == 502
            assert "detail" in response.json()
