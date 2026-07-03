"""Pydantic schemas for Wine/Proton manager API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class WineVersionResponse(BaseModel):
    """Information about a Wine/Proton version."""

    name: str
    version: str
    source: str = Field(
        description='Source: "wine-ge", "proton-ge", or "lutris-wine"',
    )
    url: str | None = None
    filename: str | None = None
    release_date: str | None = None
    is_installed: bool = False
    install_path: str | None = None


class WineInstallRequest(BaseModel):
    """Request to install a Wine/Proton version."""

    version_name: str = Field(..., min_length=1, description="Name for the version")
    version_url: str = Field(..., min_length=1, description="Download URL for the archive")


class WineDownloadProgress(BaseModel):
    """Download progress for a Wine/Proton version."""

    percentage: float = 0.0
    speed_mbps: float = 0.0
    downloaded_mb: float = 0.0
    total_mb: float = 0.0
    status: str = "unknown"
