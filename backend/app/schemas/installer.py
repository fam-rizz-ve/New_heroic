"""Pydantic schemas for installer API."""

from __future__ import annotations

from pydantic import BaseModel


class InstallerInfo(BaseModel):
    """Information about an available installer."""

    name: str
    game_slug: str
    version: str
    runner: str = "wine"
    year: str = ""
    description: str = ""
    steps: int = 0


class InstallStartRequest(BaseModel):
    """Request to start an installation."""

    manifest_yaml: str
    game_dir: str


class InstallProgress(BaseModel):
    """Progress update during installation."""

    step: int
    total_steps: int
    action: str
    description: str
    status: str = "running"
    error: str | None = None
