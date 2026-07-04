"""API endpoints for cover art management."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.covers import RefreshCoverResponse, SingleCoverResponse

router = APIRouter(prefix="/covers", tags=["covers"])


@router.post("/refresh-all")
async def refresh_all_covers() -> RefreshCoverResponse:
    """Refresh cover art for all games missing covers."""
    from app.stores.cover_service import refresh_missing_covers

    result = await refresh_missing_covers()
    return RefreshCoverResponse(**result)


@router.post("/games/{game_id}/refresh")
async def refresh_game_cover_endpoint(game_id: str) -> SingleCoverResponse:
    """Refresh cover art for a specific game."""
    from app.api.dependencies import get_use_cases
    from app.core.domain.value_objects import GameId as DomainGameId
    from app.stores.cover_service import refresh_game_cover

    try:
        gid = DomainGameId.from_str(game_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid game ID format")

    use_cases = get_use_cases()
    game = use_cases.get_game(gid)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    updated = await refresh_game_cover(game_id)

    # Re-fetch to get updated cover_art_url
    refreshed_game = use_cases.get_game(gid)
    return SingleCoverResponse(
        game_id=game_id,
        title=game.title,
        cover_art_url=refreshed_game.cover_art_url if refreshed_game else game.cover_art_url,
        updated=updated,
    )
