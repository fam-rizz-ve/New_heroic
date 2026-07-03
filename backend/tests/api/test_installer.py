"""Integration tests for installer API."""

from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
def app() -> FastAPI:
    """Create a fresh app for installer tests."""
    return create_app()


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async client for installer API tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


VALID_YAML = """
name: Test Game
game_slug: test-game
version: "1.0"
runner: wine

installer:
  - mkdir:
      description: Create directory
      path: $GAMEDIR/test_dir
"""

INVALID_YAML = """
game_slug: no-name
version: "1.0"
"""


@pytest.mark.asyncio
async def test_parse_valid_installer(client: AsyncClient) -> None:
    """POST /api/installer/parse with valid YAML returns metadata."""
    response = await client.post(
        "/api/installer/parse",
        json={"manifest_yaml": VALID_YAML, "game_dir": "/tmp/test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Game"
    assert data["game_slug"] == "test-game"
    assert data["steps"] == 1


@pytest.mark.asyncio
async def test_parse_invalid_installer(client: AsyncClient) -> None:
    """POST /api/installer/parse with invalid YAML returns 400."""
    response = await client.post(
        "/api/installer/parse",
        json={"manifest_yaml": INVALID_YAML, "game_dir": "/tmp/test"},
    )
    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_install_game(client: AsyncClient) -> None:
    """POST /api/installer/install runs an installer and returns completion."""
    response = await client.post(
        "/api/installer/install",
        json={
            "manifest_yaml": VALID_YAML,
            "game_dir": "/tmp/test_install_game",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["game"] == "Test Game"
