"""Integration tests for game and library API endpoints."""

import pytest
from httpx import AsyncClient


class TestLibraryEndpoints:
    """Tests for library CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_list_libraries_has_default(self, client: AsyncClient) -> None:
        """List libraries should return the auto-created default library."""
        response = await client.get("/api/libraries")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == "Game Library"

    @pytest.mark.asyncio
    async def test_create_library(self, client: AsyncClient) -> None:
        """Creating a library should return the created library."""
        response = await client.post(
            "/api/libraries",
            json={"name": "My Library", "store_source": "local"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Library"
        assert data["store_source"] == "local"
        assert data["game_count"] == 0
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_library_invalid_store(self, client: AsyncClient) -> None:
        """Creating a library with invalid store should return 400."""
        response = await client.post(
            "/api/libraries",
            json={"name": "Bad Lib", "store_source": "invalid_store"},
        )
        assert response.status_code == 400
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_create_and_list_libraries(self, client: AsyncClient) -> None:
        """Creating libraries should make them visible in list."""
        await client.post(
            "/api/libraries",
            json={"name": "Lib 1", "store_source": "local"},
        )
        await client.post(
            "/api/libraries",
            json={"name": "Lib 2", "store_source": "epic"},
        )
        response = await client.get("/api/libraries")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    @pytest.mark.asyncio
    async def test_list_libraries_structure(self, client: AsyncClient) -> None:
        """Library list should have correct response shape."""
        await client.post(
            "/api/libraries",
            json={"name": "Test Lib", "store_source": "local"},
        )
        response = await client.get("/api/libraries")
        data = response.json()
        lib = data[0]
        assert set(lib.keys()) == {
            "id", "name", "store_source", "game_count",
            "created_at", "updated_at",
        }


class TestGameEndpoints:
    """Tests for game CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_create_and_list_games(self, client: AsyncClient) -> None:
        """Create a library, add a game, then list games."""
        # Create library
        lib_resp = await client.post(
            "/api/libraries",
            json={"name": "Game Lib", "store_source": "local"},
        )
        lib_id = lib_resp.json()["id"]

        # Add game
        game_resp = await client.post(
            f"/api/libraries/{lib_id}/games",
            json={
                "title": "Test Game",
                "store": "local",
                "runner": "native",
            },
        )
        assert game_resp.status_code == 201
        game_data = game_resp.json()
        assert game_data["title"] == "Test Game"
        assert game_data["status"] == "not_installed"
        assert "id" in game_data

        # List games
        list_resp = await client.get(f"/api/libraries/{lib_id}/games")
        assert list_resp.status_code == 200
        games = list_resp.json()
        assert len(games) == 1
        assert games[0]["title"] == "Test Game"

    @pytest.mark.asyncio
    async def test_add_game_invalid_library(self, client: AsyncClient) -> None:
        """Adding a game to a non-existent library should return 404."""
        response = await client.post(
            "/api/libraries/00000000-0000-0000-0000-000000000000/games",
            json={
                "title": "Orphan",
                "store": "local",
                "runner": "native",
            },
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_add_game_invalid_store(self, client: AsyncClient) -> None:
        """Adding a game with invalid store should return 400."""
        # Create library first
        lib_resp = await client.post(
            "/api/libraries",
            json={"name": "Lib", "store_source": "local"},
        )
        lib_id = lib_resp.json()["id"]

        response = await client.post(
            f"/api/libraries/{lib_id}/games",
            json={
                "title": "Bad Store",
                "store": "invalid_store",
                "runner": "native",
            },
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_add_game_any_store(self, client: AsyncClient) -> None:
        """A game from any store can be added to any library (unified library)."""
        # Create epic library
        lib_resp = await client.post(
            "/api/libraries",
            json={"name": "Epic Lib", "store_source": "epic"},
        )
        lib_id = lib_resp.json()["id"]

        # Add a local game to an epic library should succeed now
        response = await client.post(
            f"/api/libraries/{lib_id}/games",
            json={
                "title": "Local Game in Epic Lib",
                "store": "local",
                "runner": "native",
            },
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_get_game(self, client: AsyncClient) -> None:
        """Getting a game should return its details."""
        # Create library and game
        lib_resp = await client.post(
            "/api/libraries",
            json={"name": "Lib", "store_source": "local"},
        )
        lib_id = lib_resp.json()["id"]

        game_resp = await client.post(
            f"/api/libraries/{lib_id}/games",
            json={
                "title": "Target Game",
                "store": "local",
                "runner": "native",
                "description": "A target game",
            },
        )
        game_id = game_resp.json()["id"]

        # Get game
        get_resp = await client.get(f"/api/games/{game_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["title"] == "Target Game"
        assert data["description"] == "A target game"
        assert data["status"] == "not_installed"
        assert data["install_path"] is None

    @pytest.mark.asyncio
    async def test_get_game_not_found(self, client: AsyncClient) -> None:
        """Getting a non-existent game should return 404."""
        response = await client.get(
            "/api/games/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404


class TestGameActions:
    """Tests for game action endpoints (install, launch, etc.)."""

    @pytest.mark.asyncio
    async def test_install_launch_close_uninstall(
        self, client: AsyncClient
    ) -> None:
        """Test the full game action lifecycle via API."""
        # Create library and game
        lib_resp = await client.post(
            "/api/libraries",
            json={"name": "Action Lib", "store_source": "local"},
        )
        lib_id = lib_resp.json()["id"]

        game_resp = await client.post(
            f"/api/libraries/{lib_id}/games",
            json={
                "title": "Action Game",
                "store": "local",
                "runner": "native",
            },
        )
        game_id = game_resp.json()["id"]

        # Install
        install_resp = await client.post(f"/api/games/{game_id}/install")
        assert install_resp.status_code == 200
        assert install_resp.json()["game"]["status"] == "installing"

        # The test notes: We don't have a complete_installation endpoint
        # in the API directly, so the lifecycle test via API is limited.
        # Use case tests cover the complete lifecycle internally.

    @pytest.mark.asyncio
    async def test_install_nonexistent_game(self, client: AsyncClient) -> None:
        """Installing a non-existent game should return 404."""
        response = await client.post(
            "/api/games/00000000-0000-0000-0000-000000000000/install"
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_uninstall_nonexistent_game(self, client: AsyncClient) -> None:
        """Uninstalling a non-existent game should return 404."""
        response = await client.post(
            "/api/games/00000000-0000-0000-0000-000000000000/uninstall"
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_launch_nonexistent_game(self, client: AsyncClient) -> None:
        """Launching a non-existent game should return 404."""
        response = await client.post(
            "/api/games/00000000-0000-0000-0000-000000000000/launch"
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_close_nonexistent_game(self, client: AsyncClient) -> None:
        """Closing a non-existent game should return 404."""
        response = await client.post(
            "/api/games/00000000-0000-0000-0000-000000000000/close"
        )
        assert response.status_code == 404


class TestGameResponseStructure:
    """Tests for game response structure compliance."""

    @pytest.mark.asyncio
    async def test_game_response_fields(self, client: AsyncClient) -> None:
        """Game response should have all required fields."""
        lib_resp = await client.post(
            "/api/libraries",
            json={"name": "Struct Lib", "store_source": "local"},
        )
        lib_id = lib_resp.json()["id"]

        game_resp = await client.post(
            f"/api/libraries/{lib_id}/games",
            json={
                "title": "Structured Game",
                "store": "local",
                "runner": "native",
            },
        )
        data = game_resp.json()
        expected_fields = {
            "id", "title", "store", "runner", "status",
            "description", "cover_art_url", "install_path",
            "executable_path", "last_played", "total_play_time_seconds",
            "is_favorite", "created_at", "updated_at",
        }
        assert set(data.keys()) == expected_fields

    @pytest.mark.asyncio
    async def test_game_action_response_fields(
        self, client: AsyncClient
    ) -> None:
        """Game action response should have message and game fields."""
        lib_resp = await client.post(
            "/api/libraries",
            json={"name": "Action Struct", "store_source": "local"},
        )
        lib_id = lib_resp.json()["id"]

        game_resp = await client.post(
            f"/api/libraries/{lib_id}/games",
            json={
                "title": "Action Game",
                "store": "local",
                "runner": "native",
            },
        )
        game_id = game_resp.json()["id"]

        action_resp = await client.post(f"/api/games/{game_id}/install")
        data = action_resp.json()
        assert "message" in data
        assert "game" in data
        game_data = data["game"]
        assert "id" in game_data
        assert "status" in game_data
