"""Shared fixtures for backend tests."""

from collections.abc import AsyncGenerator

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
