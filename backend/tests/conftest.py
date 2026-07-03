"""Shared fixtures for backend tests."""

from collections.abc import AsyncGenerator

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import create_app


@pytest.fixture
def app() -> FastAPI:
    """Create a fresh FastAPI application for testing.

    Temporarily clears ``database_url`` so that in-memory repositories
    are used (isolated per test run, no persistent state leaking between
    tests).
    """
    _orig_db_url = settings.database_url
    settings.database_url = ""
    try:
        return create_app()
    finally:
        settings.database_url = _orig_db_url


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
