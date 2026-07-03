"""Tests for EpicStore."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.stores.epic import EpicStore


@pytest.fixture
def epic_store() -> EpicStore:
    """Create an EpicStore instance for testing."""
    return EpicStore()


@pytest.mark.asyncio
async def test_authenticate_with_auth_code(epic_store: EpicStore) -> None:
    """Test successful authentication with an authorization code (--code flag)."""
    with patch.object(epic_store, "_run_command", new_callable=AsyncMock) as mock_run:
        mock_run.return_value.stdout = "Saved credentials for user@example.com"

        result = await epic_store.authenticate("test-code-123")
        assert result.token == "stored_in_legendary_config"
        assert result.username == "epic_user"
        # Verify --code flag was used (not 32 chars, so auto-detected as code)
        args = mock_run.call_args[0][0]
        assert args[0] == "auth"
        assert args[1] == "--code"
        assert args[2] == "test-code-123"


@pytest.mark.asyncio
async def test_authenticate_with_sid_fallback(epic_store: EpicStore) -> None:
    """Test successful authentication with a session id (--sid fallback).

    A 32-char alphanumeric string first tries --code. When that fails,
    it should fall back to --sid.
    """
    with patch.object(epic_store, "_run_command", new_callable=AsyncMock) as mock_run:
        # First call (--code) fails, second call (--sid) succeeds
        mock_run.side_effect = [
            RuntimeError("--code failed"),
            AsyncMock(stdout="Saved credentials for user@example.com", stderr=""),
        ]

        sid = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"
        result = await epic_store.authenticate(sid)
        assert result.token == "stored_in_legendary_config"
        assert result.username == "epic_user"
        # Verify two calls were made: first --code, then --sid
        assert mock_run.call_count == 2
        first_args = mock_run.call_args_list[0][0][0]
        assert first_args == ["auth", "--code", sid]
        second_args = mock_run.call_args_list[1][0][0]
        assert second_args == ["auth", "--sid", sid]


@pytest.mark.asyncio
async def test_authenticate_with_sid_direct(epic_store: EpicStore) -> None:
    """Test authentication with a 32-char code that works as --code.

    Since we try --code first, a 32-char alphanumeric string that works
    as an authorization code should use the --code flag.
    """
    with patch.object(epic_store, "_run_command", new_callable=AsyncMock) as mock_run:
        mock_run.return_value.stdout = "Saved credentials for user@example.com"

        code = "0255c203e189445eb9b2f966a71e3459"
        result = await epic_store.authenticate(code)
        assert result.token == "stored_in_legendary_config"
        assert result.username == "epic_user"
        # Verify --code flag was used (tried first)
        args = mock_run.call_args[0][0]
        assert args[0] == "auth"
        assert args[1] == "--code"
        assert args[2] == code


@pytest.mark.asyncio
async def test_authenticate_failure(epic_store: EpicStore) -> None:
    """Test authentication failure raises RuntimeError."""
    with patch.object(epic_store, "_run_command", new_callable=AsyncMock) as mock_run:
        mock_run.return_value.stderr = "Invalid auth code"
        mock_run.return_value.stdout = ""

        with pytest.raises(RuntimeError, match="Epic authentication failed"):
            await epic_store.authenticate("bad-code")


@pytest.mark.asyncio
async def test_authenticate_empty_code_raises(epic_store: EpicStore) -> None:
    """Test that an empty code raises ValueError."""
    with pytest.raises(ValueError, match="session id.*or.*authorization code"):
        await epic_store.authenticate("")


@pytest.mark.asyncio
async def test_is_authenticated_true(epic_store: EpicStore) -> None:
    """Test checking authentication when valid."""
    with patch.object(epic_store, "_run_command", new_callable=AsyncMock) as mock_run:
        mock_run.return_value.stdout = json.dumps({
            "account": {"id": "abc123", "name": "testuser"},
        })

        assert await epic_store.is_authenticated() is True


@pytest.mark.asyncio
async def test_is_authenticated_false(epic_store: EpicStore) -> None:
    """Test checking authentication when invalid."""
    with patch.object(epic_store, "_run_command", new_callable=AsyncMock) as mock_run:
        mock_run.return_value.stdout = "{}"

        assert await epic_store.is_authenticated() is False


@pytest.mark.asyncio
async def test_is_authenticated_cli_failure(epic_store: EpicStore) -> None:
    """Test checking authentication when CLI fails."""
    with patch.object(epic_store, "_run_command", new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = RuntimeError("CLI not found")

        assert await epic_store.is_authenticated() is False


@pytest.mark.asyncio
async def test_list_games(epic_store: EpicStore) -> None:
    """Test listing games from Epic."""
    mock_data = [
        {
            "app_name": "fortnite",
            "app_title": "Fortnite",
            "developer": "Epic Games",
        },
        {
            "app_name": "rocket_league",
            "app_title": "Rocket League",
            "developer": "Psyonix",
        },
    ]
    with patch.object(epic_store, "_run_command", new_callable=AsyncMock) as mock_run:
        mock_run.return_value.stdout = json.dumps(mock_data)

        games = await epic_store.list_games()
        assert len(games) == 2
        assert games[0].store_id == "fortnite"
        assert games[0].title == "Fortnite"
        assert games[1].store_id == "rocket_league"
        assert games[1].title == "Rocket League"


@pytest.mark.asyncio
async def test_get_game_details(epic_store: EpicStore) -> None:
    """Test getting game details."""
    mock_data = {
        "title": "Fortnite",
        "description": "A battle royale game",
        "developer": "Epic Games",
        "publisher": "Epic Games",
        "release_date": "2017-07-25",
        "metadata": {
            "genres": [{"name": "Action"}, {"name": "Battle Royale"}],
        },
    }
    with patch.object(epic_store, "_run_command", new_callable=AsyncMock) as mock_run:
        mock_run.return_value.stdout = json.dumps(mock_data)

        game = await epic_store.get_game_details("fortnite")
        assert game.title == "Fortnite"
        assert game.developer == "Epic Games"
        assert "Action" in game.genres
        assert game.release_date == "2017-07-25"


@pytest.mark.asyncio
async def test_install_game(epic_store: EpicStore) -> None:
    """Test installing a game."""
    with patch.object(epic_store, "_run_command", new_callable=AsyncMock) as mock_run:
        mock_run.return_value.stdout = "Installation complete"

        await epic_store.install_game("fortnite", "/games/epic/fortnite")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "download" in args
        assert "fortnite" in args
