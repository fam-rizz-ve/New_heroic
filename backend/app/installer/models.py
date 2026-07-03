"""Data models for game installer manifests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class InstallerFile:
    """A file to be downloaded during installation."""

    name: str
    url: str


@dataclass
class InstallerStep:
    """A single step in the installation process.

    Action types:
    - download: Download a file from URL
    - extract: Extract an archive
    - execute: Run a shell command
    - task: Run a named task (winecfg, winetricks, etc.)
    - wine: Run an executable with Wine
    - chmodx: Make a file executable
    - mkdir: Create a directory
    - rename: Move/rename files
    - require: Check that a dependency is met
    """

    action: str
    description: str = ""
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class InstallerManifest:
    """A complete installer manifest loaded from YAML."""

    name: str
    game_slug: str
    version: str
    runner: str = "wine"
    year: str = ""
    description: str = ""
    notes: str = ""
    files: list[InstallerFile] = field(default_factory=list)
    steps: list[InstallerStep] = field(default_factory=list)
