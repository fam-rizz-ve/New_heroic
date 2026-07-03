"""Integration tests for runner API endpoints."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.main import create_app


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


@pytest.mark.asyncio
async def test_list_runners(client: AsyncClient) -> None:
    """Test listing all available runners."""
    response = await client.get("/api/runners")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    names = [r["name"] for r in data]
    assert "native" in names
    assert "wine" in names
    assert "proton" in names


@pytest.mark.asyncio
async def test_detect_all_runners(client: AsyncClient) -> None:
    """Test detecting all runners."""
    response = await client.get("/api/runners/detect")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Native should always be installed
    native = next(r for r in data if r["name"] == "native")
    assert native["is_installed"] is True


@pytest.mark.asyncio
async def test_detect_nonexistent_runner(client: AsyncClient) -> None:
    """Test detecting a runner that doesn't exist."""
    response = await client.get("/api/runners/fake/detect")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_detect_specific_runner(client: AsyncClient) -> None:
    """Test detecting a specific runner."""
    response = await client.get("/api/runners/native/detect")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "native"
    assert data["is_installed"] is True
