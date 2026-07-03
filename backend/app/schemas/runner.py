"""Pydantic schemas for runner API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class RunnerInfoResponse(BaseModel):
    """Information about a runner."""

    name: str
    display_name: str
    version: str
    path: str | None = None
    is_installed: bool = False
    config: dict[str, Any] = {}
    error: str | None = None
