"""Epic Games store integration via Legendary CLI."""

from __future__ import annotations

import json
import re

import structlog

from app.stores.base import StoreBase, StoreCredentials, StoreGame


class EpicStore(StoreBase):
    """Store integration for Epic Games using the Legendary CLI."""

    name = "epic"
    display_name = "Epic Games"
    _cli_name = "legendary"
    logger = structlog.get_logger("app.stores.EpicStore")
    # sid values are typically 32-character hex/alphanumeric strings
    _SID_PATTERN = re.compile(r"^[a-zA-Z0-9]{32}$")

    async def authenticate(self, code: str) -> StoreCredentials:
        """Authenticate with Epic using an authorization code or session id.

        Auto-detects whether the provided value is an authorization code or a
        session id (sid). Both formats can be 32-character alphanumeric strings,
        so we try the standard OAuth authorization code (--code) first and fall
        back to session id (--sid) if that fails.

        Args:
            code: The authorization code or session id from Epic's OAuth flow.

        Returns:
            StoreCredentials indicating successful authentication.

        Raises:
            RuntimeError: If Legendary rejects the value.
        """
        self.logger.info("Authenticating with Epic Games")

        if not code:
            raise ValueError("A session id (sid) or authorization code is required")

        # Both authorization codes and SIDs can be 32-char alphanumeric.
        # Try --code (standard OAuth) first, fall back to --sid.
        if self._SID_PATTERN.match(code):
            self.logger.info("Trying authorization code (--code) format")
            try:
                result = await self._run_command(["auth", "--code", code])
            except RuntimeError:
                self.logger.info("Authorization code failed, trying session id (--sid)")
                result = await self._run_command(["auth", "--sid", code])
        else:
            self.logger.info("Using authorization code (--code) format")
            result = await self._run_command(["auth", "--code", code])

        if "Saved credentials" in result.stdout:
            self.logger.info("Epic Games authentication succeeded")
            return StoreCredentials(
                token="stored_in_legendary_config",
                username="epic_user",
            )
        self.logger.error("Epic Games authentication failed")
        raise RuntimeError(f"Epic authentication failed: {result.stderr}")

    async def is_authenticated(self) -> bool:
        """Check if Legendary has valid credentials."""
        self.logger.debug("Checking Epic Games auth status")
        try:
            result = await self._run_command(["status", "--json"])
            data = json.loads(result.stdout)
            authed = data.get("account") not in (None, "<not logged in>")
            self.logger.debug("Epic Games auth status", authenticated=authed)
            return authed
        except (RuntimeError, json.JSONDecodeError):
            self.logger.debug("Epic Games not authenticated")
            return False

    async def list_games(self) -> list[StoreGame]:
        """List all games in the Epic library via Legendary."""
        self.logger.info("Listing Epic Games library")
        result = await self._run_command(["list-games", "--json"])
        games_data = json.loads(result.stdout)
        games: list[StoreGame] = []
        for item in games_data:
            games.append(StoreGame(
                store_id=item.get("app_name", ""),
                title=item.get("app_title", "Unknown"),
                developer=item.get("developer", ""),
                publisher=item.get("publisher", ""),
            ))
        self.logger.info("Epic Games library listed", count=len(games))
        return games

    async def get_game_details(self, store_id: str) -> StoreGame:
        """Get detailed information about a specific Epic game.

        Args:
            store_id: The Epic app name (e.g., "fortnite").

        Returns:
            StoreGame with full metadata.

        Raises:
            RuntimeError: If Legendary cannot find the game.
        """
        self.logger.info("Getting Epic game details", store_id=store_id)
        result = await self._run_command(["info", store_id, "--json"])
        data = json.loads(result.stdout)
        genres = [
            g["name"]
            for g in data.get("metadata", {}).get("genres", [])
        ]
        return StoreGame(
            store_id=store_id,
            title=data.get("title", "Unknown"),
            description=data.get("description", ""),
            developer=data.get("developer", ""),
            publisher=data.get("publisher", ""),
            release_date=data.get("release_date"),
            genres=genres,
        )

    async def install_game(self, store_id: str, install_path: str) -> None:
        """Install an Epic game via Legendary.

        Args:
            store_id: The Epic app name.
            install_path: Directory to install the game into.

        Raises:
            RuntimeError: If the installation fails.
        """
        self.logger.info("Installing Epic game", store_id=store_id, install_path=install_path)
        await self._run_command([
            "download",
            store_id,
            "--install-dir",
            install_path,
            "--yes",
        ])

    async def get_auth_url(self) -> str:
        """Return the Epic Games OAuth login URL.

        Returns:
            The URL to open for browser-based OAuth login.
        """
        return "https://www.epicgames.com/id/login?redirectUrl=https://www.epicgames.com/id/api/redirect"

    async def get_auth_instructions(self) -> str:
        """Return instructions for Epic Games OAuth login.

        Returns:
            Human-readable login steps.
        """
        return (
            "1. Open the Epic Games login URL in your browser.\n"
            "2. Log in with your Epic Games account.\n"
            "3. After logging in, you will be redirected to a page "
            "(the URL will look like "
            "'https://epicgames.com/account/personal?sid=XXXX').\n"
            "4. Copy the 'sid' value from the URL and paste it here."
        )
