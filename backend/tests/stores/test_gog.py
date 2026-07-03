"""Tests for GOGStore."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.stores.gog import GOGStore

# ---- Fixtures ----


@pytest.fixture
def gog_store() -> GOGStore:
    """Create a GOGStore instance for testing."""
    return GOGStore()


# ---- authenticate ----


@pytest.mark.asyncio
async def test_authenticate(gog_store: GOGStore) -> None:
    """Test successful authentication via direct HTTP token exchange."""
    mock_response = Mock()
    mock_response.is_success = True
    mock_response.json.return_value = {
        "access_token": "gog_access_token_123",
        "refresh_token": "gog_refresh_token_456",
        "expires_in": 3600,
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with (
        patch("app.stores.gog.httpx.AsyncClient") as mock_client_cls,
        patch.object(gog_store, "_save_credentials") as mock_save,
        patch("app.stores.gog.time.time", return_value=1000),
    ):
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        result = await gog_store.authenticate("test-code-456")
        assert result.token == "gog_access_token_123"

        # Verify it called the correct token URL
        called_url = mock_client.get.call_args[0][0]
        assert "auth.gog.com/token" in called_url
        assert "client_id=46899977096215655" in called_url
        assert "code=test-code-456" in called_url

        # Verify credentials were saved with loginTime
        mock_save.assert_called_once_with(
            GOGStore.CLIENT_ID,
            {
                "access_token": "gog_access_token_123",
                "refresh_token": "gog_refresh_token_456",
                "expires_in": 3600,
                "loginTime": 1000,
            },
        )


@ pytest.mark.asyncio
async def test_authenticate_http_error(gog_store: GOGStore) -> None:
    """Test authenticate raises RuntimeError on HTTP error."""
    mock_response = Mock()
    mock_response.is_success = False
    mock_response.status_code = 400

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with patch("app.stores.gog.httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        with pytest.raises(RuntimeError, match="GOG rejected the authorization code: 400"):
            await gog_store.authenticate("bad-code")


@ pytest.mark.asyncio
async def test_authenticate_api_error(gog_store: GOGStore) -> None:
    """Test authenticate raises RuntimeError on GOG error response."""
    mock_response = Mock()
    mock_response.is_success = True
    mock_response.json.return_value = {
        "error": "invalid_grant",
        "error_description": "Authorization code has expired",
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with patch("app.stores.gog.httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        with pytest.raises(RuntimeError, match="Authorization code has expired"):
            await gog_store.authenticate("expired-code")


@ pytest.mark.asyncio
async def test_authenticate_request_error(gog_store: GOGStore) -> None:
    """Test authenticate raises RuntimeError on network error."""
    import httpx

    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.RequestError("Connection refused")

    with patch("app.stores.gog.httpx.AsyncClient") as mock_client_cls:
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        with pytest.raises(RuntimeError, match="GOG auth request failed: Connection refused"):
            await gog_store.authenticate("network-error")


# ---- is_authenticated ----


@pytest.mark.asyncio
async def test_is_authenticated_true(gog_store: GOGStore) -> None:
    """Test is_authenticated returns True when valid token exists."""
    with patch.object(
        gog_store, "_get_valid_access_token", return_value="valid_token_123",
    ):
        assert await gog_store.is_authenticated() is True


@pytest.mark.asyncio
async def test_is_authenticated_false(gog_store: GOGStore) -> None:
    """Test is_authenticated returns False when token is None."""
    with patch.object(
        gog_store, "_get_valid_access_token", return_value=None,
    ):
        assert await gog_store.is_authenticated() is False


# ---- _get_valid_access_token / _read_credentials ----


@pytest.mark.asyncio
async def test_read_credentials_no_config(gog_store: GOGStore) -> None:
    """Test _read_credentials returns None when config file does not exist."""
    with patch.object(gog_store, "_get_config_path", return_value="/tmp/nonexistent/config.json"):
        assert gog_store._read_credentials() is None


@pytest.mark.asyncio
async def test_read_credentials_invalid_json(gog_store: GOGStore) -> None:
    """Test _read_credentials returns None on invalid JSON."""
    with (
        patch.object(gog_store, "_get_config_path", return_value="/tmp/bad_config.json"),
        patch("builtins.open", new_callable=AsyncMock) as mock_open,
    ):
        mock_open.return_value.__enter__.return_value.read.return_value = "not json"
        assert gog_store._read_credentials() is None


@pytest.mark.asyncio
async def test_get_valid_access_token_not_authenticated(gog_store: GOGStore) -> None:
    """Test _get_valid_access_token returns None when no credentials."""
    with patch.object(gog_store, "_read_credentials", return_value=None):
        assert gog_store._get_valid_access_token() is None


@pytest.mark.asyncio
async def test_get_valid_access_token_valid(gog_store: GOGStore) -> None:
    """Test _get_valid_access_token returns existing token when not expired."""
    credentials = {
        "access_token": "my_valid_token",
        "loginTime": 1000,
        "expires_in": 999999,  # far in the future
    }
    with (
        patch.object(gog_store, "_read_credentials", return_value=credentials),
        patch("app.stores.gog.time.time", return_value=500),  # well before expiry
    ):
        token = gog_store._get_valid_access_token()
        assert token == "my_valid_token"


@pytest.mark.asyncio
async def test_get_valid_access_token_expired_no_refresh(gog_store: GOGStore) -> None:
    """Test _get_valid_access_token returns None when expired and no refresh_token."""
    credentials = {
        "access_token": "expired_token",
        "loginTime": 0,
        "expires_in": 1,  # expired long ago
    }
    with patch.object(gog_store, "_read_credentials", return_value=credentials):
        token = gog_store._get_valid_access_token()
        assert token is None


# ---- list_games ----


@pytest.mark.asyncio
async def test_list_games_not_authenticated(gog_store: GOGStore) -> None:
    """Test list_games raises RuntimeError when not authenticated."""
    with patch.object(gog_store, "_get_valid_access_token", return_value=None):
        with pytest.raises(RuntimeError, match="Not authenticated with GOG"):
            await gog_store.list_games()


@pytest.mark.asyncio
async def test_list_games_success(gog_store: GOGStore) -> None:
    """Test list_games fetches and parses games from GOG API."""
    mock_token = "valid_token"

    # Simulate httpx responses (use Mock, not AsyncMock, because
    # response.json() is a synchronous method in the real httpx)
    mock_owned_response = Mock()
    mock_owned_response.is_success = True
    mock_owned_response.json.return_value = {"owned": [1207664643, 1904626354]}

    mock_detail_1 = Mock()
    mock_detail_1.is_success = True
    mock_detail_1.json.return_value = {
        "title": "The Witcher 3: Wild Hunt",
        "description": "An open-world RPG",
        "image": "https://images.gog.com/witcher3.jpg",
        "developer": "CD Projekt Red",
        "publisher": "CD Projekt",
        "releaseDate": "2015-05-19",
        "genres": [{"name": "RPG"}, {"name": "Action"}],
    }

    mock_detail_2 = Mock()
    mock_detail_2.is_success = True
    mock_detail_2.json.return_value = {
        "title": "Cyberpunk 2077",
        "description": "Open-world sci-fi RPG",
        "image": "https://images.gog.com/cyberpunk.jpg",
        "developer": "CD Projekt Red",
        "publisher": "CD Projekt",
        "releaseDate": "2020-12-10",
        "genres": [{"name": "RPG"}, {"name": "Sci-fi"}],
    }

    mock_client = AsyncMock()
    mock_client.get.side_effect = [
        mock_owned_response,
        mock_detail_1,
        mock_detail_2,
    ]

    with (
        patch.object(gog_store, "_get_valid_access_token", return_value=mock_token),
        patch("app.stores.gog.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        games = await gog_store.list_games()
        assert len(games) == 2
        assert games[0].title == "The Witcher 3: Wild Hunt"
        assert games[0].store_id == "1207664643"
        assert games[0].developer == "CD Projekt Red"
        assert games[0].description == "An open-world RPG"
        assert games[0].genres == ["RPG", "Action"]
        assert games[1].title == "Cyberpunk 2077"
        assert games[1].store_id == "1904626354"

        # Verify the API calls
        assert mock_client.get.call_count == 3
        mock_client.get.assert_any_call(
            f"{GOGStore.GOG_EMBED}/user/data/games",
        )
        mock_client.get.assert_any_call(
            f"{GOGStore.GOG_EMBED}/account/gameDetails/1207664643.json",
            timeout=10,
        )
        mock_client.get.assert_any_call(
            f"{GOGStore.GOG_EMBED}/account/gameDetails/1904626354.json",
            timeout=10,
        )


@pytest.mark.asyncio
async def test_list_games_api_error(gog_store: GOGStore) -> None:
    """Test list_games raises RuntimeError on API failure."""
    mock_token = "valid_token"

    mock_response = Mock()
    mock_response.is_success = False
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with (
        patch.object(gog_store, "_get_valid_access_token", return_value=mock_token),
        patch("app.stores.gog.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        with pytest.raises(RuntimeError, match="GOG API error: 401"):
            await gog_store.list_games()


@pytest.mark.asyncio
async def test_list_games_skips_failed_details(gog_store: GOGStore) -> None:
    """Test list_games skips games whose detail fetch fails."""
    mock_token = "valid_token"

    mock_owned_response = Mock()
    mock_owned_response.is_success = True
    mock_owned_response.json.return_value = {"owned": [1, 2]}

    # First detail succeeds, second fails
    mock_detail_ok = Mock()
    mock_detail_ok.is_success = True
    mock_detail_ok.json.return_value = {
        "title": "Game 1",
        "genres": [],
    }

    mock_detail_fail = Mock()
    mock_detail_fail.is_success = False
    mock_detail_fail.status_code = 404
    mock_detail_fail.text = "Not Found"

    mock_client = AsyncMock()
    mock_client.get.side_effect = [
        mock_owned_response,
        mock_detail_ok,
        mock_detail_fail,
    ]

    with (
        patch.object(gog_store, "_get_valid_access_token", return_value=mock_token),
        patch("app.stores.gog.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        games = await gog_store.list_games()
        assert len(games) == 1
        assert games[0].title == "Game 1"


# ---- get_game_details ----


@pytest.mark.asyncio
async def test_get_game_details_not_authenticated(gog_store: GOGStore) -> None:
    """Test get_game_details raises RuntimeError when not authenticated."""
    with patch.object(gog_store, "_get_valid_access_token", return_value=None):
        with pytest.raises(RuntimeError, match="Not authenticated with GOG"):
            await gog_store.get_game_details("123")


@pytest.mark.asyncio
async def test_get_game_details_success(gog_store: GOGStore) -> None:
    """Test get_game_details fetches and parses game details from GOG API."""
    mock_token = "valid_token"
    mock_data = {
        "title": "The Witcher 3: Wild Hunt",
        "description": "An open-world RPG",
        "image": "https://images.gog.com/witcher3.jpg",
        "developer": "CD Projekt Red",
        "publisher": "CD Projekt",
        "releaseDate": "2015-05-19",
        "genres": [{"name": "RPG"}, {"name": "Action"}],
    }

    mock_response = Mock()
    mock_response.is_success = True
    mock_response.json.return_value = mock_data

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with (
        patch.object(gog_store, "_get_valid_access_token", return_value=mock_token),
        patch("app.stores.gog.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        game = await gog_store.get_game_details("1207664643")
        assert game.title == "The Witcher 3: Wild Hunt"
        assert game.store_id == "1207664643"
        assert game.developer == "CD Projekt Red"
        assert game.publisher == "CD Projekt"
        assert game.description == "An open-world RPG"
        assert game.cover_art_url == "https://images.gog.com/witcher3.jpg"
        assert game.release_date == "2015-05-19"
        assert game.genres == ["RPG", "Action"]

        mock_client.get.assert_called_once_with(
            f"{GOGStore.GOG_EMBED}/account/gameDetails/1207664643.json",
        )


@pytest.mark.asyncio
async def test_get_game_details_api_error(gog_store: GOGStore) -> None:
    """Test get_game_details raises RuntimeError on API failure."""
    mock_token = "valid_token"

    mock_response = Mock()
    mock_response.is_success = False
    mock_response.status_code = 404
    mock_response.text = "Not Found"

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with (
        patch.object(gog_store, "_get_valid_access_token", return_value=mock_token),
        patch("app.stores.gog.httpx.AsyncClient") as mock_client_cls,
    ):
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        with pytest.raises(RuntimeError, match="GOG API error: 404"):
            await gog_store.get_game_details("999")


# ---- install_game ----


@pytest.mark.asyncio
async def test_install_game(gog_store: GOGStore) -> None:
    """Test installing a game via gogdl."""
    with patch.object(gog_store, "_run_command", new_callable=AsyncMock) as mock_run:
        mock_run.return_value.stdout = "Download complete"

        await gog_store.install_game("123", "/games/gog/witcher3")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "--auth-config-path"
        assert args[2] == "download"
        assert "123" in args


# ---- get_auth_url ----


@pytest.mark.asyncio
async def test_get_auth_url(gog_store: GOGStore) -> None:
    """Test get_auth_url returns correct OAuth URL."""
    url = await gog_store.get_auth_url()
    assert GOGStore.CLIENT_ID in url
    assert "auth.gog.com/auth" in url
    assert "response_type=code" in url


# ---- get_auth_instructions ----


@pytest.mark.asyncio
async def test_get_auth_instructions(gog_store: GOGStore) -> None:
    """Test get_auth_instructions returns login steps."""
    instructions = await gog_store.get_auth_instructions()
    assert "GOG" in instructions
    assert "code" in instructions


# ---- _gogdl_args ----


def test_gogdl_args(gog_store: GOGStore) -> None:
    """Test _gogdl_args prepends --auth-config-path."""
    with patch.object(
        gog_store, "_ensure_config_dir", return_value="/tmp/test_config.json",
    ):
        result = gog_store._gogdl_args(["download", "123"])
        assert result[0] == "--auth-config-path"
        assert result[1] == "/tmp/test_config.json"
        assert result[2] == "download"
        assert result[3] == "123"
