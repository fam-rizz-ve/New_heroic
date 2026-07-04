"""Tests for SteamStore."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.stores.steam import SteamStore


@pytest.fixture
def steam_store() -> SteamStore:
    """Create a SteamStore instance for testing."""
    return SteamStore()


@pytest.mark.asyncio
async def test_check_installed_found(steam_store: SteamStore) -> None:
    """Test check_installed returns True when Steam directory exists."""
    with patch.object(Path, "exists", return_value=True):
        with patch.object(Path, "__truediv__", return_value=MagicMock()) as mock_div:
            mock_div.return_value.exists.return_value = True
            result = await steam_store.check_installed()
            assert result is True
            assert steam_store._steam_dir is not None


@pytest.mark.asyncio
async def test_check_installed_not_found(steam_store: SteamStore) -> None:
    """Test check_installed returns False when Steam is not installed."""
    with patch.object(Path, "exists", return_value=False):
        result = await steam_store.check_installed()
        assert result is False
        assert steam_store._steam_dir is None


@pytest.mark.asyncio
async def test_is_authenticated_no_steam(steam_store: SteamStore) -> None:
    """Test is_authenticated returns False when Steam not installed."""
    with patch.object(Path, "exists", return_value=False):
        result = await steam_store.is_authenticated()
        assert result is False


@pytest.mark.asyncio
async def test_is_authenticated_steam_found(steam_store: SteamStore) -> None:
    """Test is_authenticated returns True when Steam is installed."""
    steam_store._steam_dir = Path("/fake/steam")
    result = await steam_store.is_authenticated()
    assert result is True


@pytest.mark.asyncio
async def test_authenticate_raises_not_implemented(steam_store: SteamStore) -> None:
    """Test authenticate raises NotImplementedError."""
    with pytest.raises(NotImplementedError, match="does not require authentication"):
        await steam_store.authenticate("test-code")


@pytest.mark.asyncio
async def test_install_game_raises_not_implemented(steam_store: SteamStore) -> None:
    """Test install_game raises NotImplementedError."""
    with pytest.raises(NotImplementedError, match="read-only"):
        await steam_store.install_game("123456", "/fake/path")


@pytest.mark.asyncio
async def test_get_auth_url_raises_not_implemented(steam_store: SteamStore) -> None:
    """Test get_auth_url raises NotImplementedError."""
    with pytest.raises(NotImplementedError, match="does not use OAuth"):
        await steam_store.get_auth_url()


@pytest.mark.asyncio
async def test_get_auth_instructions_raises_not_implemented(
    steam_store: SteamStore,
) -> None:
    """Test get_auth_instructions raises NotImplementedError."""
    with pytest.raises(NotImplementedError, match="does not require authentication"):
        await steam_store.get_auth_instructions()


@pytest.mark.asyncio
async def test_list_games_no_steam(steam_store: SteamStore) -> None:
    """Test list_games raises RuntimeError when Steam not installed."""
    with patch.object(Path, "exists", return_value=False):
        with pytest.raises(RuntimeError, match="not installed"):
            await steam_store.list_games()


@pytest.mark.asyncio
async def test_list_games_success(steam_store: SteamStore) -> None:
    """Test list_games returns parsed games from ACF files."""
    # Set up steam directory
    steam_store._steam_dir = Path("/fake/steam")

    # Mock library folders — use real Path objects so sorted() works
    mock_acf_1 = Path("/fake/steam/steamapps/appmanifest_123456.acf")
    mock_acf_2 = Path("/fake/steam/steamapps/appmanifest_789012.acf")

    # Mock vdf data for first ACF
    vdf_data_1 = {
        "AppState": {
            "appid": "123456",
            "name": "Test Game One",
        }
    }

    # Mock vdf data for second ACF
    vdf_data_2 = {
        "AppState": {
            "appid": "789012",
            "name": "Test Game Two",
            "SizeOnDisk": "12345678",
        }
    }

    with (
        patch.object(steam_store, "_get_library_folders") as mock_folders,
        patch("builtins.open", new_callable=MagicMock),
        patch("vdf.load") as mock_vdf_load,
    ):
        # Return a single library folder
        lib_dir = Path("/fake/steam")
        mock_folders.return_value = [lib_dir]

        # Mock steamapps directory exists
        steamapps_dir = MagicMock(spec=Path)
        steamapps_dir.exists.return_value = True
        steamapps_dir.glob.return_value = [mock_acf_1, mock_acf_2]

        with patch.object(Path, "__truediv__", return_value=steamapps_dir):
            # Return different vdf data for each call
            mock_vdf_load.side_effect = [vdf_data_1, vdf_data_2]

            games = await steam_store.list_games()

            assert len(games) == 2
            assert games[0].store_id == "123456"
            assert games[0].title == "Test Game One"
            assert "123456" in games[0].cover_art_url
            assert games[1].store_id == "789012"
            assert games[1].title == "Test Game Two"


@pytest.mark.asyncio
async def test_list_games_invalid_acf(steam_store: SteamStore) -> None:
    """Test list_games skips ACF files with missing required fields."""
    steam_store._steam_dir = Path("/fake/steam")

    mock_acf = MagicMock(spec=Path)
    mock_acf.name = "appmanifest_000000.acf"

    with (
        patch.object(steam_store, "_get_library_folders") as mock_folders,
        patch("builtins.open", new_callable=MagicMock),
        patch("vdf.load") as mock_vdf_load,
    ):
        lib_dir = Path("/fake/steam")
        mock_folders.return_value = [lib_dir]

        steamapps_dir = MagicMock(spec=Path)
        steamapps_dir.exists.return_value = True
        steamapps_dir.glob.return_value = [mock_acf]

        with patch.object(Path, "__truediv__", return_value=steamapps_dir):
            # ACF with missing name field
            mock_vdf_load.return_value = {"AppState": {"appid": "000000", "name": ""}}
            games = await steam_store.list_games()
            assert len(games) == 0


@pytest.mark.asyncio
async def test_get_game_details_found(steam_store: SteamStore) -> None:
    """Test get_game_details returns StoreGame for an existing app ID."""
    steam_store._steam_dir = Path("/fake/steam")

    with (
        patch.object(steam_store, "_get_library_folders") as mock_folders,
        patch("builtins.open", new_callable=MagicMock),
        patch("vdf.load") as mock_vdf_load,
        patch.object(Path, "exists") as mock_exists,
    ):
        lib_dir = Path("/fake/steam")
        mock_folders.return_value = [lib_dir]

        # The ACF file exists
        mock_exists.side_effect = lambda: True

        acf_path = MagicMock(spec=Path)
        acf_path.exists.return_value = True

        vdf_data = {
            "AppState": {
                "appid": "123456",
                "name": "Found Game",
            }
        }
        mock_vdf_load.return_value = vdf_data

        with patch.object(Path, "__truediv__", return_value=acf_path):
            game = await steam_store.get_game_details("123456")
            assert game.store_id == "123456"
            assert game.title == "Found Game"


@pytest.mark.asyncio
async def test_get_game_details_not_found(steam_store: SteamStore) -> None:
    """Test get_game_details raises RuntimeError for missing app ID."""
    steam_store._steam_dir = Path("/fake/steam")

    with (
        patch.object(steam_store, "_get_library_folders") as mock_folders,
        patch.object(Path, "exists", return_value=False),
    ):
        lib_dir = Path("/fake/steam")
        mock_folders.return_value = [lib_dir]

        with pytest.raises(RuntimeError, match="not found"):
            await steam_store.get_game_details("999999")


@pytest.mark.asyncio
async def test_get_library_folders_main_only(steam_store: SteamStore) -> None:
    """Test _get_library_folders returns main dir when VDF missing."""
    steam_store._steam_dir = Path("/fake/steam")

    with patch.object(Path, "exists", return_value=False):
        folders = steam_store._get_library_folders()
        assert len(folders) == 1
        assert folders[0] == Path("/fake/steam")


@pytest.mark.asyncio
async def test_get_library_folders_with_vdf(steam_store: SteamStore) -> None:
    """Test _get_library_folders parses VDF for extra paths."""
    steam_store._steam_dir = Path("/fake/steam")

    vdf_data = {
        "libraryfolders": {
            "0": {"path": "/extra/steam/library"},
            "1": {"path": "/another/steam/library"},
        }
    }

    with (
        patch.object(Path, "exists") as mock_exists,
        patch("builtins.open", new_callable=MagicMock),
        patch("vdf.load") as mock_vdf_load,
    ):
        # Main steamapps dir, VDF file, and extra dirs all exist
        def exists_side_effect() -> bool:
            return True

        mock_exists.side_effect = exists_side_effect
        mock_vdf_load.return_value = vdf_data

        folders = steam_store._get_library_folders()
        # Main dir + 2 VDF paths = 3
        assert len(folders) == 3
        assert Path("/fake/steam") in folders
        assert Path("/extra/steam/library") in folders
        assert Path("/another/steam/library") in folders


@pytest.mark.asyncio
async def test_parse_acf_valid(steam_store: SteamStore) -> None:
    """Test _parse_acf returns StoreGame for valid ACF data."""
    acf_path = Path("/fake/manifest.acf")

    with (
        patch("builtins.open", new_callable=MagicMock),
        patch("vdf.load") as mock_vdf_load,
    ):
        mock_vdf_load.return_value = {
            "AppState": {
                "appid": "123456",
                "name": "Valid Game",
            }
        }

        game = steam_store._parse_acf(acf_path)
        assert game is not None
        assert game.store_id == "123456"
        assert game.title == "Valid Game"
        assert "123456" in game.cover_art_url


@pytest.mark.asyncio
async def test_parse_acf_invalid(steam_store: SteamStore) -> None:
    """Test _parse_acf returns None for invalid ACF content."""
    acf_path = Path("/fake/manifest.acf")

    with (
        patch("builtins.open", new_callable=MagicMock),
        patch("vdf.load") as mock_vdf_load,
    ):
        mock_vdf_load.side_effect = Exception("Parse error")
        game = steam_store._parse_acf(acf_path)
        assert game is None


@pytest.mark.asyncio
async def test_parse_acf_missing_name(steam_store: SteamStore) -> None:
    """Test _parse_acf returns None when ACF has empty name."""
    acf_path = Path("/fake/manifest.acf")

    with (
        patch("builtins.open", new_callable=MagicMock),
        patch("vdf.load") as mock_vdf_load,
    ):
        mock_vdf_load.return_value = {
            "AppState": {"appid": "000000", "name": ""}
        }
        game = steam_store._parse_acf(acf_path)
        assert game is None


@pytest.mark.asyncio
async def test_list_games_dedup_app_id(steam_store: SteamStore) -> None:
    """Test list_games deduplicates games with same app_id across folders."""
    steam_store._steam_dir = Path("/fake/steam")

    # Two ACF files with the same app_id (simulates same game in two library folders)
    mock_acf_1 = Path("/fake/steam/steamapps/appmanifest_123456.acf")

    vdf_data = {
        "AppState": {
            "appid": "123456",
            "name": "Duplicated Game",
        }
    }

    with (
        patch.object(steam_store, "_get_library_folders") as mock_folders,
        patch("builtins.open", new_callable=MagicMock),
        patch("vdf.load") as mock_vdf_load,
    ):
        # Two library folders, both containing the same app
        lib_dir_1 = Path("/fake/steam")
        lib_dir_2 = Path("/extra/steam/library")
        mock_folders.return_value = [lib_dir_1, lib_dir_2]

        # Mock steamapps dirs
        steamapps_dir_1 = MagicMock(spec=Path)
        steamapps_dir_1.exists.return_value = True
        steamapps_dir_1.glob.return_value = [mock_acf_1]

        steamapps_dir_2 = MagicMock(spec=Path)
        steamapps_dir_2.exists.return_value = True
        steamapps_dir_2.glob.return_value = [mock_acf_1]

        def truediv_side_effect(key: str) -> MagicMock:
            return steamapps_dir_1 if key == "steamapps" else steamapps_dir_2

        with patch.object(Path, "__truediv__", side_effect=truediv_side_effect):
            mock_vdf_load.return_value = vdf_data

            games = await steam_store.list_games()

            # Only 1 game despite 2 folders with same manifest
            assert len(games) == 1
            assert games[0].store_id == "123456"
            assert games[0].title == "Duplicated Game"


@pytest.mark.asyncio
async def test_parse_acf_proton_filter(steam_store: SteamStore) -> None:
    """Test _parse_acf returns None for Proton compatibility tool."""
    acf_path = Path("/fake/proton.acf")

    with (
        patch("builtins.open", new_callable=MagicMock),
        patch("vdf.load") as mock_vdf_load,
    ):
        mock_vdf_load.return_value = {
            "AppState": {
                "appid": "123456",
                "name": "Proton 9.0",
            }
        }

        game = steam_store._parse_acf(acf_path)
        assert game is None


@pytest.mark.asyncio
async def test_parse_acf_linux_runtime_filter(steam_store: SteamStore) -> None:
    """Test _parse_acf returns None for Steam Linux Runtime tool."""
    acf_path = Path("/fake/runtime.acf")

    with (
        patch("builtins.open", new_callable=MagicMock),
        patch("vdf.load") as mock_vdf_load,
    ):
        mock_vdf_load.return_value = {
            "AppState": {
                "appid": "987654",
                "name": "Steam Linux Runtime - Soldier",
            }
        }

        game = steam_store._parse_acf(acf_path)
        assert game is None


@pytest.mark.asyncio
async def test_parse_acf_real_game(steam_store: SteamStore) -> None:
    """Test _parse_acf returns StoreGame for a real game (not a tool)."""
    acf_path = Path("/fake/game.acf")

    with (
        patch("builtins.open", new_callable=MagicMock),
        patch("vdf.load") as mock_vdf_load,
    ):
        mock_vdf_load.return_value = {
            "AppState": {
                "appid": "730",
                "name": "Counter-Strike 2",
            }
        }

        game = steam_store._parse_acf(acf_path)
        assert game is not None
        assert game.store_id == "730"
        assert game.title == "Counter-Strike 2"
        assert "730" in game.cover_art_url
