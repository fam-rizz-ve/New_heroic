"""Runner manager for discovering and accessing game runners."""

from __future__ import annotations

from typing import Any

import structlog

from app.runners.base import RunnerBase
from app.runners.native import NativeRunner
from app.runners.proton import ProtonRunner
from app.runners.wine import WineRunner


class RunnerManager:
    """Registry and factory for game runners."""

    def __init__(self) -> None:
        self._runners: dict[str, RunnerBase] = {}
        self.logger = structlog.get_logger("app.runners.RunnerManager")

    def register(self, runner: RunnerBase) -> None:
        """Register a runner."""
        self._runners[runner.name] = runner
        self.logger.debug("Runner registered", runner=runner.name)

    def get(self, name: str) -> RunnerBase | None:
        """Get a runner by name."""
        runner = self._runners.get(name)
        if runner:
            self.logger.debug("Runner accessed", runner=name)
        return runner

    def list_available(self) -> list[dict[str, Any]]:
        """List all registered runners with their info."""
        result: list[dict[str, Any]] = []
        for name, runner in self._runners.items():
            result.append({
                "name": name,
                "display_name": runner.display_name,
            })
        return result

    async def detect_all(self) -> list[dict[str, Any]]:
        """Detect all registered runners and return their status."""
        results: list[dict[str, Any]] = []
        for name, runner in self._runners.items():
            try:
                info = await runner.detect()
                results.append({
                    "name": name,
                    "display_name": runner.display_name,
                    "version": info.version,
                    "path": info.path,
                    "is_installed": info.is_installed,
                    "config": info.config,
                })
            except Exception as e:
                self.logger.error("Failed to detect runner", runner=name, error=str(e))
                results.append({
                    "name": name,
                    "display_name": runner.display_name,
                    "version": "",
                    "path": None,
                    "is_installed": False,
                    "error": str(e),
                })
        return results

    @classmethod
    def create_default(cls) -> RunnerManager:
        """Create a RunnerManager with all standard runners registered."""
        manager = cls()
        manager.register(NativeRunner())
        manager.register(WineRunner())
        manager.register(ProtonRunner())
        manager.logger.info("Default runners registered", count=len(manager._runners))
        return manager
