"""Pydantic schemas for per-game settings API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GameSettingsResponse(BaseModel):
    """Per-game configuration exposed via the API."""

    game_id: str
    runner: str = "wine"
    wine_version: str | None = None
    wine_prefix: str | None = None
    wine_arch: str = "win64"
    arguments: str = ""
    env_vars: dict[str, str] = Field(default_factory=dict)
    dxvk: bool = True
    vkd3d: bool = True
    fsr: bool = False
    fsr_quality: str = "ultra"
    use_steam_runtime: bool = False
    game_mode: bool = True
    mangohud: bool = False
    pre_launch_command: str = ""
    post_exit_command: str = ""


class GameSettingsUpdateRequest(BaseModel):
    """Request to update per-game settings.

    All fields are optional — only provided fields are updated.
    """

    runner: str | None = None
    wine_version: str | None = None
    wine_prefix: str | None = None
    wine_arch: str | None = None
    arguments: str | None = None
    env_vars: dict[str, str] | None = None
    dxvk: bool | None = None
    vkd3d: bool | None = None
    fsr: bool | None = None
    fsr_quality: str | None = None
    use_steam_runtime: bool | None = None
    game_mode: bool | None = None
    mangohud: bool | None = None
    pre_launch_command: str | None = None
    post_exit_command: str | None = None
