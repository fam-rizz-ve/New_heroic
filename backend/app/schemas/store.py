"""Pydantic schemas for store API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class StoreInfo(BaseModel):
    """Information about a store integration."""

    name: str
    display_name: str


class StoreGameSchema(BaseModel):
    """Game metadata from a store."""

    store_id: str
    title: str
    description: str = ""
    cover_art_url: str = ""
    developer: str = ""
    publisher: str = ""
    release_date: str | None = None
    genres: list[str] = Field(default_factory=list)


class AuthRequest(BaseModel):
    """Authentication request for a store."""

    code: str = Field(..., min_length=1, description="Auth code or token")


class AuthResponse(BaseModel):
    """Authentication response."""

    success: bool
    username: str | None = None
    message: str = ""


class SyncResult(BaseModel):
    """Result of syncing a store library."""

    imported: int = 0
    total: int = 0
    message: str = ""


class AuthUrlResponse(BaseModel):
    """Response containing a store's OAuth login URL."""

    auth_url: str
    instructions: str
    store_name: str


class StoreStatusResponse(BaseModel):
    """Status information for a store integration."""

    name: str
    display_name: str
    is_authenticated: bool
    is_installed: bool
