"""Pydantic schemas for the cover art system."""

from pydantic import BaseModel


class RefreshCoverResponse(BaseModel):
    """Response for batch cover refresh."""

    refreshed: int
    failed: int
    total_checked: int = 0


class SingleCoverResponse(BaseModel):
    """Response for single game cover refresh."""

    game_id: str
    title: str
    cover_art_url: str | None = None
    updated: bool
