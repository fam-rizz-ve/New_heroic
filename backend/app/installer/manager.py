"""Installer manager for discovering and running game installers."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import structlog

from app.installer.executor import InstallExecutor
from app.installer.models import InstallerManifest
from app.installer.parser import load_installer_file, parse_installer

logger = structlog.get_logger(__name__)


class InstallerManager:
    """Manages game installer manifests and their execution."""

    def __init__(self, installers_dir: str | None = None) -> None:
        self.installers_dir = Path(installers_dir) if installers_dir else None
        self._active_installations: dict[str, InstallExecutor] = {}

    def parse_installer(self, yaml_content: str) -> InstallerManifest:
        """Parse a YAML installer string."""
        return parse_installer(yaml_content)

    async def run_installer(
        self,
        manifest: InstallerManifest,
        game_dir: str,
        on_progress: Callable[[int, int, str, str], None] | None = None,
    ) -> None:
        """Run a full installation from a manifest."""
        executor = InstallExecutor(manifest, game_dir)
        self._active_installations[manifest.game_slug] = executor

        try:
            await executor.execute(on_progress=on_progress)
        finally:
            self._active_installations.pop(manifest.game_slug, None)

    def cancel_installation(self, game_slug: str) -> bool:
        """Cancel a running installation."""
        executor = self._active_installations.get(game_slug)
        if executor:
            executor.cancel()
            return True
        return False

    def list_available_installers(self) -> list[dict[str, Any]]:
        """List installer YAML files in the installers directory."""
        if not self.installers_dir or not self.installers_dir.exists():
            return []

        installers: list[dict[str, Any]] = []
        for yaml_file in self.installers_dir.glob("*.yaml"):
            try:
                manifest = load_installer_file(yaml_file)
                installers.append(
                    {
                        "name": manifest.name,
                        "game_slug": manifest.game_slug,
                        "version": manifest.version,
                        "runner": manifest.runner,
                        "year": manifest.year,
                        "description": manifest.description,
                        "steps": len(manifest.steps),
                    }
                )
            except Exception as e:
                logger.error(
                    "Failed to parse installer",
                    file=str(yaml_file),
                    error=str(e),
                )

        return installers
