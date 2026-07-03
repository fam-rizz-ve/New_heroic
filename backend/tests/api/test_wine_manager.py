"""Integration tests for wine manager API endpoints."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.wine_manager import get_wine_manager
from app.main import create_app
from app.runners.wine_manager import WineVersion


@pytest.fixture
def app() -> FastAPI:
    """Create the FastAPI application for testing."""
    return create_app()


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _mock_wine_manager(
    app: FastAPI,
    mock_manager: MagicMock,
) -> None:
    """Override the wine manager dependency with a mock."""
    app.dependency_overrides[get_wine_manager] = lambda: mock_manager


class TestWineManagerEndpoints:
    """Tests for /api/wine/* endpoints."""

    @pytest.mark.asyncio
    async def test_list_installed_empty(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        """GET /api/wine/installed should return an empty list when none installed."""
        mock_manager = MagicMock()
        mock_manager.list_installed_versions.return_value = []
        _mock_wine_manager(app, mock_manager)

        response = await client.get("/api/wine/installed")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_list_installed_with_versions(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        """GET /api/wine/installed should return installed versions."""
        mock_manager = MagicMock()
        mock_manager.list_installed_versions.return_value = [
            WineVersion(
                name="Wine-GE-8-25",
                version="Wine-GE-8-25",
                source="wine-ge",
                url=None,
                filename=None,
                is_installed=True,
                install_path="/home/user/.config/new_heroic/tools/Wine-GE-8-25",
            ),
        ]
        _mock_wine_manager(app, mock_manager)

        response = await client.get("/api/wine/installed")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Wine-GE-8-25"
        assert data[0]["source"] == "wine-ge"
        assert data[0]["is_installed"] is True

    @pytest.mark.asyncio
    async def test_get_download_progress(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        """GET /api/wine/downloads/{name} should return progress."""
        mock_manager = MagicMock()
        mock_manager.get_download_progress.return_value = {
            "percentage": 50.0,
            "speed_mbps": 1.0,
            "downloaded_mb": 50.0,
            "total_mb": 100.0,
            "status": "downloading",
        }
        _mock_wine_manager(app, mock_manager)

        response = await client.get("/api/wine/downloads/Wine-GE-8-25")
        assert response.status_code == 200
        data = response.json()
        assert data["percentage"] == 50.0
        assert data["status"] == "downloading"

    @pytest.mark.asyncio
    async def test_get_download_progress_none(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        """GET /api/wine/downloads/{name} should return null when not tracked."""
        mock_manager = MagicMock()
        mock_manager.get_download_progress.return_value = None
        _mock_wine_manager(app, mock_manager)

        response = await client.get("/api/wine/downloads/untracked")
        assert response.status_code == 200
        data = response.json()
        assert data is None

    @pytest.mark.asyncio
    async def test_delete_version_success(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        """DELETE /api/wine/versions/{name} should return 204."""
        mock_manager = MagicMock()
        mock_manager.delete_version = AsyncMock()
        _mock_wine_manager(app, mock_manager)

        response = await client.delete("/api/wine/versions/Wine-GE-8-25")
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_version_not_found(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        """DELETE /api/wine/versions/{name} should return 404 for missing version."""
        mock_manager = MagicMock()
        mock_manager.delete_version = AsyncMock(
            side_effect=FileNotFoundError("not installed"),
        )
        _mock_wine_manager(app, mock_manager)

        response = await client.delete("/api/wine/versions/nonexistent")
        assert response.status_code == 404
        assert "not installed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_install_version_success(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        """POST /api/wine/install should return the install path."""
        mock_manager = MagicMock()
        mock_manager.download_version = AsyncMock(
            return_value="/home/user/.config/new_heroic/tools/Wine-GE-8-25",
        )
        _mock_wine_manager(app, mock_manager)

        response = await client.post(
            "/api/wine/install",
            json={
                "version_name": "Wine-GE-8-25",
                "version_url": "https://example.com/wine-ge-8-25.tar.xz",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "path" in data
        assert "Wine-GE-8-25" in data["path"]

    @pytest.mark.asyncio
    async def test_install_version_failure(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        """POST /api/wine/install should return 500 on error."""
        mock_manager = MagicMock()
        mock_manager.download_version = AsyncMock(
            side_effect=RuntimeError("Download failed"),
        )
        _mock_wine_manager(app, mock_manager)

        response = await client.post(
            "/api/wine/install",
            json={
                "version_name": "bad-version",
                "version_url": "https://example.com/bad.tar.xz",
            },
        )
        assert response.status_code == 500
        assert "Download failed" in response.json()["detail"]
