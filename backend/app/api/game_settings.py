"""API endpoints for per-game settings."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.game_settings import GameSettingsStore
from app.schemas.game_settings import (
    GameSettingsResponse,
    GameSettingsUpdateRequest,
)

router = APIRouter(prefix="/games", tags=["game_settings"])

# Module-level singleton; replaced with DI wiring in production.
_store: GameSettingsStore | None = None


def get_settings_store() -> GameSettingsStore:
    """Dependency: get the GameSettingsStore singleton."""
    global _store
    if _store is None:
        _store = GameSettingsStore()
    return _store


@router.get(
    "/{game_id}/settings",
    response_model=GameSettingsResponse,
)
async def get_game_settings(
    game_id: str,
    store: GameSettingsStore = Depends(get_settings_store),
) -> GameSettingsResponse:
    """Get per-game settings for a specific game.

    Returns default settings if none have been saved yet.

    Args:
        game_id: The game identifier.

    Returns:
        GameSettingsResponse with current settings.
    """
    settings = store.get_settings(game_id)
    return GameSettingsResponse(
        game_id=settings.game_id,
        runner=settings.runner,
        wine_version=settings.wine_version,
        wine_prefix=settings.wine_prefix,
        wine_arch=settings.wine_arch,
        arguments=settings.arguments,
        env_vars=settings.env_vars,
        dxvk=settings.dxvk,
        vkd3d=settings.vkd3d,
        fsr=settings.fsr,
        fsr_quality=settings.fsr_quality,
        use_steam_runtime=settings.use_steam_runtime,
        game_mode=settings.game_mode,
        mangohud=settings.mangohud,
        pre_launch_command=settings.pre_launch_command,
        post_exit_command=settings.post_exit_command,
    )


@router.put(
    "/{game_id}/settings",
    response_model=GameSettingsResponse,
)
async def update_game_settings(
    game_id: str,
    request: GameSettingsUpdateRequest,
    store: GameSettingsStore = Depends(get_settings_store),
) -> GameSettingsResponse:
    """Update per-game settings for a specific game.

    Only the fields provided in the request body are updated;
    missing fields retain their current values.

    Args:
        game_id: The game identifier.
        request: Partial or full GameSettingsUpdateRequest.

    Returns:
        GameSettingsResponse with the updated settings.

    Raises:
        HTTPException 500: If settings cannot be saved.
    """
    current = store.get_settings(game_id)

    # Apply updates only for non-None fields
    update_data = request.model_dump(exclude_none=True)
    for field_name, value in update_data.items():
        setattr(current, field_name, value)

    try:
        store.save_settings(current)
    except OSError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save settings: {e}",
        )

    return GameSettingsResponse(
        game_id=current.game_id,
        runner=current.runner,
        wine_version=current.wine_version,
        wine_prefix=current.wine_prefix,
        wine_arch=current.wine_arch,
        arguments=current.arguments,
        env_vars=current.env_vars,
        dxvk=current.dxvk,
        vkd3d=current.vkd3d,
        fsr=current.fsr,
        fsr_quality=current.fsr_quality,
        use_steam_runtime=current.use_steam_runtime,
        game_mode=current.game_mode,
        mangohud=current.mangohud,
        pre_launch_command=current.pre_launch_command,
        post_exit_command=current.post_exit_command,
    )
