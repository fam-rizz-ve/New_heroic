"""GOG store integration via gogdl CLI and GOG API."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx
import structlog

from app.stores.base import StoreBase, StoreCredentials, StoreGame


class GOGStore(StoreBase):
    """Store integration for GOG using gogdl CLI and GOG API."""

    name = "gog"
    display_name = "GOG"
    _cli_name = "gogdl"
    logger = structlog.get_logger("app.stores.GOGStore")

    # GOG OAuth constants (from gogdl source code)
    CLIENT_ID = "46899977096215655"
    CLIENT_SECRET = "9d85c43b1482497dbbce61f6e4aa173a433796eeae2ca8c5f6129f2dc4de46d9"
    GOG_EMBED = "https://embed.gog.com"
    GOG_AUTH = "https://auth.gog.com"

    @staticmethod
    def _get_config_dir() -> str:
        """Get gogdl config directory (matches gogdl's CONFIG_DIR logic).

        Returns:
            Path to the gogdl config directory.
        """
        config_home = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        gogdl_config_path = os.getenv("GOGDL_CONFIG_PATH")
        if gogdl_config_path:
            return os.path.join(gogdl_config_path, "heroic_gogdl")
        return os.path.join(config_home, "heroic_gogdl")

    @staticmethod
    def _get_config_path() -> str:
        """Get full path to gogdl config JSON file.

        Returns:
            Full path to the config.json file.
        """
        return os.path.join(GOGStore._get_config_dir(), "config.json")

    def _ensure_config_dir(self) -> str:
        """Ensure the gogdl config directory and file exist.

        Returns:
            Path to the config file.
        """
        config_dir = self._get_config_dir()
        Path(config_dir).mkdir(parents=True, exist_ok=True)
        config_path = self._get_config_path()
        if not os.path.exists(config_path):
            with open(config_path, "w") as f:
                json.dump({}, f)
        return config_path

    def _gogdl_args(self, args: list[str]) -> list[str]:
        """Prepend the auth config path to gogdl arguments.

        Args:
            args: The gogdl command arguments.

        Returns:
            Full argument list with --auth-config-path prepended.
        """
        config_path = self._ensure_config_dir()
        return ["--auth-config-path", config_path, *args]

    async def _run_gogdl_command(
        self, args: list[str], input_data: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Run gogdl with the auth config path prepended.

        Args:
            args: The gogdl command arguments.
            input_data: Optional data to send to stdin.

        Returns:
            The result from _run_command.

        Raises:
            RuntimeError: If the gogdl command fails.
        """
        return await self._run_command(
            self._gogdl_args(args), input_data=input_data,
        )

    def _read_credentials(self) -> dict[str, Any] | None:
        """Read GOG credentials from gogdl config file.

        Returns:
            The credential dict for CLIENT_ID, or None if not found.
        """
        config_path = self._get_config_path()
        if not os.path.exists(config_path):
            return None
        try:
            with open(config_path) as f:
                all_data: dict[str, Any] = json.load(f)
            creds: object = all_data.get(self.CLIENT_ID)
            if isinstance(creds, dict):
                return creds
            return None
        except (json.JSONDecodeError, OSError) as e:
            self.logger.warning("Failed to read gogdl config", error=str(e))
            return None

    def _get_valid_access_token(self) -> str | None:
        """Get a valid GOG access token, refreshing if necessary.

        Returns:
            A valid access token string, or None if not authenticated.
        """
        credentials = self._read_credentials()
        if not credentials:
            return None

        login_time = credentials.get("loginTime", 0)
        expires_in = credentials.get("expires_in", 0)

        # Refresh 60 seconds early to avoid edge cases
        if time.time() >= login_time + expires_in - 60:
            refresh_token = credentials.get("refresh_token")
            if not refresh_token:
                self.logger.warning("No refresh token available")
                return None

            try:
                refresh_url = (
                    f"{self.GOG_AUTH}/token?"
                    f"client_id={self.CLIENT_ID}&"
                    f"client_secret={self.CLIENT_SECRET}&"
                    f"grant_type=refresh_token&"
                    f"refresh_token={refresh_token}"
                )
                response = httpx.get(refresh_url, timeout=10)
                if response.is_success:
                    new_data: dict[str, Any] = response.json()
                    new_data["loginTime"] = time.time()
                    self._save_credentials(self.CLIENT_ID, new_data)
                    refreshed_token: str | None = new_data.get("access_token")
                    return refreshed_token
                else:
                    self.logger.warning(
                        "Failed to refresh GOG token",
                        status=response.status_code,
                    )
                    return None
            except httpx.RequestError as e:
                self.logger.error("GOG token refresh failed", error=str(e))
                return None

        access_token: str | None = credentials.get("access_token")
        return access_token

    def _save_credentials(self, client_id: str, data: dict[str, Any]) -> None:
        """Save credentials to gogdl config file.

        Args:
            client_id: The GOG client ID to key the credentials under.
            data: The credential data to save.
        """
        config_path = self._get_config_path()
        all_data: dict[str, Any] = {}
        try:
            if os.path.exists(config_path):
                with open(config_path) as f:
                    all_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            all_data = {}
        all_data[client_id] = data
        with open(config_path, "w") as f:
            json.dump(all_data, f, indent=2)

    async def authenticate(self, code: str) -> StoreCredentials:
        """Authenticate with GOG using an authorization code.

        Exchanges the code directly via HTTP (faster than gogdl CLI)
        and stores the resulting credentials in the gogdl config file.

        Args:
            code: The GOG authorization code from the OAuth redirect.

        Returns:
            StoreCredentials indicating successful authentication.

        Raises:
            RuntimeError: If GOG rejects the code or the request fails.
        """
        self.logger.info("Authenticating with GOG")

        token_url = (
            f"{self.GOG_AUTH}/token?"
            f"client_id={self.CLIENT_ID}&"
            f"client_secret={self.CLIENT_SECRET}&"
            f"grant_type=authorization_code&"
            f"redirect_uri=https%3A%2F%2Fembed.gog.com%2Fon_login_success%3Forigin%3Dclient&"
            f"code={code}"
        )

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(token_url)

            if not response.is_success:
                raise RuntimeError(
                    f"GOG rejected the authorization code: {response.status_code}",
                )

            data: dict[str, Any] = response.json()
            if data.get("error"):
                error_msg = data.get(
                    "error_description",
                    data.get("error", "unknown error"),
                )
                raise RuntimeError(f"GOG auth error: {error_msg}")

            data["loginTime"] = time.time()
            self._save_credentials(self.CLIENT_ID, data)
            self.logger.info("GOG authentication succeeded")
            return StoreCredentials(token=data.get("access_token", ""))

        except httpx.RequestError as e:
            self.logger.error("GOG auth request failed", error=str(e))
            raise RuntimeError(f"GOG auth request failed: {e}") from e

    async def is_authenticated(self) -> bool:
        """Check if gogdl has valid credentials.

        Returns:
            True if a valid access token is available, False otherwise.
        """
        self.logger.debug("Checking GOG auth status")
        token = self._get_valid_access_token()
        self.logger.debug("GOG auth status", authenticated=token is not None)
        return token is not None

    async def list_games(self) -> list[StoreGame]:
        """List all GOG games in the user's library.

        Uses the GOG API directly with the access token since gogdl
        has no CLI command for listing owned games.

        Returns:
            A list of StoreGame objects.

        Raises:
            RuntimeError: If not authenticated or the GOG API fails.
        """
        self.logger.info("Listing GOG library via API")

        token = self._get_valid_access_token()
        if not token:
            raise RuntimeError("Not authenticated with GOG")

        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient(headers=headers, timeout=30) as client:
            # Step 1: Get owned game IDs
            self.logger.debug("Fetching owned game IDs")
            response = await client.get(f"{self.GOG_EMBED}/user/data/games")
            if not response.is_success:
                raise RuntimeError(
                    f"GOG API error: {response.status_code} - {response.text}",
                )

            owned_ids: list[int] = response.json().get("owned", [])
            self.logger.info("Found GOG games", count=len(owned_ids))

            # Step 2: Get details for each game
            games: list[StoreGame] = []
            for game_id in owned_ids:
                try:
                    detail_response = await client.get(
                        f"{self.GOG_EMBED}/account/gameDetails/{game_id}.json",
                        timeout=10,
                    )
                    if detail_response.is_success:
                        data = detail_response.json()
                        # Guard: GOG API may return an empty list for some games
                        if not isinstance(data, dict):
                            self.logger.warning(
                                "GOG game details format unexpected",
                                game_id=game_id,
                                data_type=type(data).__name__,
                            )
                            continue

                        genres = [
                            g["name"]
                            for g in data.get("genres", []) if isinstance(g, dict)
                        ]
                        # GOG embeds use backgroundImage, not image
                        image = data.get("image", "") or data.get("backgroundImage", "") or ""
                        games.append(StoreGame(
                            store_id=str(game_id),
                            title=data.get("title", f"GOG Game {game_id}"),
                            description=data.get("description", ""),
                            cover_art_url=image,
                            developer=data.get("developer", ""),
                            publisher=data.get("publisher", ""),
                            # GOG uses releaseTimestamp instead of releaseDate
                            release_date=data.get("releaseDate") or data.get("releaseTimestamp"),
                            genres=genres,
                        ))
                    else:
                        self.logger.warning(
                            "Failed to fetch GOG game details",
                            game_id=game_id,
                            status=detail_response.status_code,
                        )
                except httpx.RequestError as e:
                    self.logger.warning(
                        "Request failed for GOG game",
                        game_id=game_id,
                        error=str(e),
                    )

            self.logger.info("GOG library parsed", count=len(games))
            return games

    async def get_game_details(self, store_id: str) -> StoreGame:
        """Get detailed information about a specific GOG game.

        Args:
            store_id: The GOG game ID.

        Returns:
            StoreGame with full metadata.

        Raises:
            RuntimeError: If not authenticated or the GOG API fails.
        """
        self.logger.info("Getting GOG game details", store_id=store_id)

        token = self._get_valid_access_token()
        if not token:
            raise RuntimeError("Not authenticated with GOG")

        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient(headers=headers, timeout=10) as client:
            response = await client.get(
                f"{self.GOG_EMBED}/account/gameDetails/{store_id}.json",
            )
            if not response.is_success:
                raise RuntimeError(
                    f"GOG API error: {response.status_code} - {response.text}",
                )

            data = response.json()
            genres = [
                g["name"]
                for g in data.get("genres", []) if isinstance(g, dict)
            ]
            return StoreGame(
                store_id=store_id,
                title=data.get("title", "Unknown"),
                description=data.get("description", ""),
                cover_art_url=data.get("image", ""),
                developer=data.get("developer", ""),
                publisher=data.get("publisher", ""),
                release_date=data.get("releaseDate"),
                genres=genres,
            )

    async def install_game(self, store_id: str, install_path: str) -> None:
        """Install a GOG game via gogdl.

        Args:
            store_id: The GOG game ID.
            install_path: Directory to install the game into.

        Raises:
            RuntimeError: If the installation fails.
        """
        self.logger.info(
            "Installing GOG game",
            store_id=store_id,
            install_path=install_path,
        )
        await self._run_gogdl_command([
            "download",
            store_id,
            "--path",
            install_path,
        ])

    async def get_auth_url(self) -> str:
        """Return the GOG OAuth login URL.

        Returns:
            The URL to open for browser-based OAuth login.
        """
        redirect_encoded = (
            "https%3A%2F%2Fembed.gog.com%2Fon_login_success%3Forigin%3Dclient"
        )
        return (
            f"https://auth.gog.com/auth?"
            f"client_id={self.CLIENT_ID}&"
            f"redirect_uri={redirect_encoded}&"
            f"response_type=code"
        )

    async def get_auth_instructions(self) -> str:
        """Return instructions for GOG OAuth Login.

        Returns:
            Human-readable login steps.
        """
        return (
            "1. Open the GOG login URL in your browser.\n"
            "2. Log in with your GOG account.\n"
            "3. After logging in, you will be redirected to a page "
            "(the URL will look like "
            "'https://embed.gog.com/on_login_success?origin=client&code=XXXX').\n"
            "4. Copy the 'code' value from the URL and paste it here."
        )
