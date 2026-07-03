"""Base classes and types for game runners."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import structlog


@dataclass
class RunnerInfo:
    """Information about a runner installation."""

    name: str
    display_name: str
    version: str
    path: str | None = None
    is_installed: bool = False
    config: dict[str, Any] = field(default_factory=dict)


class RunnerBase(ABC):
    """Abstract base for game runners.

    Subclasses define how to detect, configure, and launch games
    with a specific runner (Wine, Proton, Native, etc.).
    """

    name: str = ""
    display_name: str = ""
    logger: structlog.stdlib.BoundLogger

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        cls.logger = structlog.get_logger(f"app.runners.{cls.__name__}")

    @abstractmethod
    async def detect(self) -> RunnerInfo:
        """Detect runner installation and return version info."""
        ...

    @abstractmethod
    async def run_game(
        self,
        executable: str,
        args: list[str] | None = None,
        env_vars: dict[str, str] | None = None,
    ) -> None:
        """Launch a game with this runner."""
        ...

    @abstractmethod
    async def get_settings(self) -> dict[str, Any]:
        """Get current runner configuration."""
        ...

    @abstractmethod
    async def set_setting(self, key: str, value: str) -> None:
        """Set a runner configuration value."""
        ...
