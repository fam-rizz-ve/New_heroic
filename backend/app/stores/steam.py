"""Steam store integration for importing local Steam library.

Read-only integration that scans local Steam installation directories
for game manifests (ACF files) and returns game metadata.
No authentication or installation support.
"""

from __future__ import annotations

from pathlib import Path

import structlog
import vdf

from app.stores.base import StoreBase, StoreCredentials, StoreGame


class SteamStore(StoreBase):
    """Steam game library import (read-only, no install/launch).

    Discovers games from local Steam installation by parsing
    libraryfolders.vdf and appmanifest_*.acf files.
    Does not require authentication or a CLI tool.
    """

    name = "steam"
    display_name = "Steam"
    _cli_name = ""
    logger = structlog.get_logger("app.stores.SteamStore")

    # Common Steam installation paths on Linux
    _STEAM_PATHS = [
        Path.home() / ".steam" / "steam",
        Path.home() / ".local" / "share" / "Steam",
        Path.home() / ".steam" / "root",
        Path("/usr/share/steam"),
        Path("/opt/steam"),
    ]

    def __init__(self) -> None:
        """Initialize the Steam store."""
        self._steam_dir: Path | None = None

    async def check_installed(self) -> bool:
        """Check if Steam is installed by looking for common directories."""
        for path in self._STEAM_PATHS:
            if path.exists() and (path / "steamapps").exists():
                self._steam_dir = path
                return True
        return False

    async def is_authenticated(self) -> bool:
        """Steam import is local-only, no authentication needed."""
        if not self._steam_dir and not await self.check_installed():
            return False
        return True

    async def authenticate(self, code: str) -> StoreCredentials:
        """Not supported — Steam import is local-only."""
        raise NotImplementedError(
            "Steam import is read-only and does not require authentication."
        )

    async def list_games(self) -> list[StoreGame]:
        """List all games in the local Steam library.

        Scans all Steam library folders for ACF manifest files.

        Returns:
            A list of StoreGame objects for all found games.

        Raises:
            RuntimeError: If Steam is not installed.
        """
        if not self._steam_dir:
            if not await self.check_installed():
                raise RuntimeError("Steam is not installed on this system")

        games: list[StoreGame] = []
        library_folders = self._get_library_folders()

        for folder in library_folders:
            steamapps_dir = folder / "steamapps"
            if not steamapps_dir.exists():
                continue

            for acf_file in sorted(steamapps_dir.glob("appmanifest_*.acf")):
                game = self._parse_acf(acf_file)
                if game:
                    games.append(game)

        return games

    async def get_game_details(self, store_id: str) -> StoreGame:
        """Get details for a specific Steam game by app ID.

        Args:
            store_id: The Steam app ID.

        Returns:
            StoreGame for the specified game.

        Raises:
            RuntimeError: If Steam is not installed or the game is not found.
        """
        if not self._steam_dir:
            if not await self.check_installed():
                raise RuntimeError("Steam is not installed on this system")

        library_folders = self._get_library_folders()
        acf_filename = f"appmanifest_{store_id}.acf"

        for folder in library_folders:
            acf_path = folder / "steamapps" / acf_filename
            if acf_path.exists():
                game = self._parse_acf(acf_path)
                if game:
                    return game

        raise RuntimeError(
            f"Steam game with app ID '{store_id}' not found in any library folder"
        )

    async def install_game(self, store_id: str, install_path: str) -> None:
        """Not supported — Steam import is read-only."""
        raise NotImplementedError(
            "Steam import is read-only. Use the Steam client to install games."
        )

    async def get_auth_url(self) -> str:
        """Not applicable — Steam import is local-only."""
        raise NotImplementedError("Steam import does not use OAuth.")

    async def get_auth_instructions(self) -> str:
        """Not applicable."""
        raise NotImplementedError("Steam import does not require authentication.")

    def _get_library_folders(self) -> list[Path]:
        """Get all Steam library folders by parsing libraryfolders.vdf.

        Returns:
            List of Path objects pointing to Steam library root directories.
        """
        folders: list[Path] = []

        if not self._steam_dir:
            return folders

        # The main Steam directory is always a library
        folders.append(self._steam_dir)

        # Parse libraryfolders.vdf for additional library paths
        vdf_path = self._steam_dir / "steamapps" / "libraryfolders.vdf"
        if vdf_path.exists():
            try:
                data = vdf.load(str(vdf_path))
                # libraryfolders.vdf format:
                # "libraryfolders"
                # {
                #     "0" { "path" "/some/path" ... }
                #     "1" { "path" "/other/path" ... }
                # }
                libraryfolders = data.get("libraryfolders", {})
                for key, value in libraryfolders.items():
                    if isinstance(value, dict) and "path" in value:
                        path = Path(value["path"])
                        if path.exists():
                            folders.append(path)
            except Exception:
                self.logger.warning(
                    "Failed to parse libraryfolders.vdf",
                    path=str(vdf_path),
                    exc_info=True,
                )

        # Deduplicate while preserving order
        seen: set[Path] = set()
        unique_folders: list[Path] = []
        for f in folders:
            if f not in seen:
                seen.add(f)
                unique_folders.append(f)
        return unique_folders

    def _parse_acf(self, acf_path: Path) -> StoreGame | None:
        """Parse a Steam ACF manifest file into a StoreGame.

        Args:
            acf_path: Path to the appmanifest_*.acf file.

        Returns:
            StoreGame if parsing succeeds, None if the file
            is invalid or lacks required fields.
        """
        try:
            data = vdf.load(str(acf_path))
            app_state = data.get("AppState", {})

            app_id = str(app_state.get("appid", "") or "")
            name = str(app_state.get("name", "") or "")

            if not app_id or not name:
                self.logger.warning(
                    "ACF file missing required fields",
                    path=str(acf_path),
                    app_id=app_id,
                    name=name,
                )
                return None

            cover_art_url = (
                f"https://steamcdn-a.akamaihd.net/steam/apps/"
                f"{app_id}/library_600x900.jpg"
            )

            return StoreGame(
                store_id=app_id,
                title=name,
                cover_art_url=cover_art_url,
            )
        except Exception:
            self.logger.warning(
                "Failed to parse ACF file",
                path=str(acf_path),
                exc_info=True,
            )
            return None
