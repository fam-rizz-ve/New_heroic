"""Pydantic schemas for game API requests and responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class GameCreate(BaseModel):
    """Request schema for creating a new game."""

    title: str = Field(
        ..., min_length=1, max_length=200, description="Game title"
    )
    store: str = Field(..., description="Store source: epic, gog, steam, itch, local")
    runner: str = Field(
        ..., description="Runner type: wine, proton, proton_ge, native"
    )
    description: str = Field(default="", description="Game description")
    cover_art_url: str = Field(default="", description="URL to cover artwork")


class GameResponse(BaseModel):
    """Response schema for a game."""

    id: str
    title: str
    store: str
    runner: str
    status: str
    description: str
    cover_art_url: str
    install_path: str | None = None
    executable_path: str | None = None
    last_played: datetime | None = None
    total_play_time_seconds: int = 0
    created_at: datetime
    updated_at: datetime


class GameActionResponse(BaseModel):
    """Response schema for game actions (install, launch, etc.)."""

    message: str
    game: GameResponse


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str


class LibraryCreate(BaseModel):
    """Request schema for creating a library."""

    name: str = Field(..., min_length=1, max_length=100)
    store_source: str = Field(..., description="Store source for this library")


class LibraryResponse(BaseModel):
    """Response schema for a library."""

    id: str
    name: str
    store_source: str
    game_count: int
    created_at: datetime
    updated_at: datetime
