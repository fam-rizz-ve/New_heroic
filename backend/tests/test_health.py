"""Tests for the health check endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient) -> None:
    """Test that the health endpoint returns a successful response."""
    response = await client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert data["app_name"] == "New Heroic"


@pytest.mark.asyncio
async def test_health_response_structure(client: AsyncClient) -> None:
    """Test that the health response has the expected shape."""
    response = await client.get("/api/health")
    data = response.json()

    # All required fields present
    assert "status" in data
    assert "version" in data
    assert "app_name" in data
    # No unexpected fields
    assert set(data.keys()) == {"status", "version", "app_name"}
