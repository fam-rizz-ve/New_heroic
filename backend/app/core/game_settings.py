"""Per-game settings storage and management.

Each game can have custom runner, Wine version, arguments,
environment variables, and DXVK/VKD3D toggles. Settings are
persisted as individual JSON files on disk.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import structlog

SETTINGS_DIR = os.path.expanduser("~/.config/new_heroic/game_settings")


@dataclass
class GameSettings:
    """Per-game configuration options.

    Attributes:
        game_id: Unique identifier for the game.
        runner: Runner type ("wine", "proton", "native").
        wine_version: Specific Wine/Proton version name (e.g., "GE-Proton8-25").
        wine_prefix: Custom WINEPREFIX path for Wine/Proton games.
        wine_arch: Wine architecture ("win64" or "win32").
        arguments: Additional command-line arguments for the game.
        env_vars: Environment variables to set when launching.
        dxvk: Enable DXVK (DirectX to Vulkan translation).
        vkd3d: Enable VKD3D (DirectX 12 to Vulkan translation).
        fsr: Enable FSR (FidelityFX Super Resolution) upscaling.
        fsr_quality: FSR quality preset ("ultra", "quality", "balanced",
                     "performance").
        use_steam_runtime: Use Steam Linux runtime (Lutris feature).
        game_mode: Enable Feral GameMode for CPU governor optimization.
        mangohud: Enable MangoHud performance overlay.
        pre_launch_command: Command to run before launching the game.
        post_exit_command: Command to run after the game exits.
    """

    game_id: str
    runner: str = "wine"
    wine_version: str | None = None
    wine_prefix: str | None = None
    wine_arch: str = "win64"
    arguments: str = ""
    env_vars: dict[str, str] = field(default_factory=dict)
    dxvk: bool = True
    vkd3d: bool = True
    fsr: bool = False
    fsr_quality: str = "ultra"
    use_steam_runtime: bool = False
    game_mode: bool = True
    mangohud: bool = False
    pre_launch_command: str = ""
    post_exit_command: str = ""


class GameSettingsStore:
    """Persist per-game settings as JSON files on disk.

    Each game gets its own JSON file named ``{game_id}.json`` inside
    SETTINGS_DIR. Missing files return default GameSettings.
    """

    def __init__(self) -> None:
        self.logger = structlog.get_logger("app.core.GameSettingsStore")
        os.makedirs(SETTINGS_DIR, exist_ok=True)

    def _settings_path(self, game_id: str) -> str:
        """Return the filesystem path for a game's settings file.

        Args:
            game_id: The game identifier.

        Returns:
            The absolute path to the JSON settings file.

        Raises:
            ValueError: If game_id contains path traversal characters.
        """
        if "/" in game_id or "\\" in game_id or ".." in game_id:
            raise ValueError(f"Invalid game_id: {game_id!r}")
        return os.path.join(SETTINGS_DIR, f"{game_id}.json")

    def get_settings(self, game_id: str) -> GameSettings:
        """Load settings for a specific game.

        Returns default GameSettings when no saved settings exist.

        Args:
            game_id: The game identifier.

        Returns:
            A GameSettings instance with saved or default values.
        """
        path = self._settings_path(game_id)
        if not os.path.isfile(path):
            self.logger.debug(
                "No saved settings found, using defaults",
                game_id=game_id,
            )
            return GameSettings(game_id=game_id)

        try:
            with open(path) as f:
                data = json.load(f)
            self.logger.debug("Settings loaded", game_id=game_id)
            return GameSettings(**data)
        except (json.JSONDecodeError, OSError) as e:
            self.logger.error(
                "Failed to load settings, using defaults",
                game_id=game_id,
                error=str(e),
            )
            return GameSettings(game_id=game_id)

    def save_settings(self, settings: GameSettings) -> None:
        """Save settings for a game to disk.

        Args:
            settings: The GameSettings instance to persist.

        Raises:
            OSError: If the settings file cannot be written.
        """
        path = self._settings_path(settings.game_id)
        try:
            with open(path, "w") as f:
                json.dump(
                    {
                        "game_id": settings.game_id,
                        "runner": settings.runner,
                        "wine_version": settings.wine_version,
                        "wine_prefix": settings.wine_prefix,
                        "wine_arch": settings.wine_arch,
                        "arguments": settings.arguments,
                        "env_vars": settings.env_vars,
                        "dxvk": settings.dxvk,
                        "vkd3d": settings.vkd3d,
                        "fsr": settings.fsr,
                        "fsr_quality": settings.fsr_quality,
                        "use_steam_runtime": settings.use_steam_runtime,
                        "game_mode": settings.game_mode,
                        "mangohud": settings.mangohud,
                        "pre_launch_command": settings.pre_launch_command,
                        "post_exit_command": settings.post_exit_command,
                    },
                    f,
                    indent=2,
                )
            self.logger.debug(
                "Settings saved",
                game_id=settings.game_id,
            )
        except OSError:
            self.logger.exception(
                "Failed to save settings",
                game_id=settings.game_id,
            )
            raise

    def delete_settings(self, game_id: str) -> None:
        """Remove a game's settings file from disk.

        Args:
            game_id: The game identifier.

        Raises:
            FileNotFoundError: If no settings file exists for the game.
            OSError: If the file cannot be deleted.
        """
        path = self._settings_path(game_id)
        if not os.path.isfile(path):
            raise FileNotFoundError(
                f"No settings found for game '{game_id}'"
            )
        os.remove(path)
        self.logger.debug(
            "Settings deleted",
            game_id=game_id,
        )
