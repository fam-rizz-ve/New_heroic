"""API integration tests for diagnostics endpoints."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
def app() -> FastAPI:
    """Create a fresh FastAPI app."""
    return create_app()


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with LifespanManager(app):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


class TestDiagnosticsAPI:
    """Tests for diagnostics API endpoints."""

    async def test_analyze_text(self, client: AsyncClient) -> None:
        """POST /api/diagnostics/analyze should return issues."""
        response = await client.post(
            "/api/diagnostics/analyze",
            json={
                "log_content": 'err:module:import_dll: Library xinput1_3.dll not found\n',
                "runner": "wine",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "issues" in data
        assert "summary" in data
        assert data["runner"] == "wine"
        assert len(data["issues"]) > 0

    async def test_analyze_text_clean(self, client: AsyncClient) -> None:
        """POST /api/diagnostics/analyze with clean log should return no issues."""
        response = await client.post(
            "/api/diagnostics/analyze",
            json={
                "log_content": "normal log message\n",
                "runner": "wine",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["issues"]) == 0

    async def test_analyze_text_invalid(self, client: AsyncClient) -> None:
        """POST with missing fields should return 422."""
        response = await client.post(
            "/api/diagnostics/analyze",
            json={"log_content": "test"},
            # missing "runner"
        )
        assert response.status_code == 422

    async def test_analyze_text_empty_content(self, client: AsyncClient) -> None:
        """POST with empty log content should be accepted but return no issues."""
        response = await client.post(
            "/api/diagnostics/analyze",
            json={"log_content": "", "runner": "wine"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["issues"]) == 0

    async def test_list_patterns(self, client: AsyncClient) -> None:
        """GET /api/diagnostics/patterns should return patterns."""
        response = await client.get("/api/diagnostics/patterns")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Each pattern should have required fields
        for pattern in data:
            assert "name" in pattern
            assert "description" in pattern
            assert "issue_type" in pattern
            assert "severity" in pattern
            assert "title" in pattern
            assert "suggestion" in pattern
