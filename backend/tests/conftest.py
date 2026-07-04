"""Shared fixtures for backend tests."""

from collections.abc import AsyncGenerator, Generator

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import create_app


@pytest.fixture
def app() -> Generator[FastAPI, None, None]:
    """Create a fresh FastAPI application for testing.

    Temporarily clears ``database_url`` so that in-memory repositories
    are used (isolated per test run, no persistent state leaking between
    tests).

    Also resets the ``get_use_cases`` singleton (``dependencies._use_cases``)
    so that each test run gets fresh in-memory repositories. Without this
    reset, the singleton persists across tests, causing data leakage and
    flaky assertions (e.g., expecting exactly 1 game when previous tests
    added games to the same in-memory store).
    """
    import app.api.dependencies as deps

    _orig_db_url = settings.database_url
    _orig_use_cases = deps._use_cases

    # Force fresh in-memory repositories for this test
    deps._use_cases = None
    settings.database_url = ""
    app = create_app()
    try:
        yield app
    finally:
        settings.database_url = _orig_db_url
        deps._use_cases = _orig_use_cases


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
