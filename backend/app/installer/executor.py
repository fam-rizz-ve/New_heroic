"""Sequential executor for installer steps."""

from __future__ import annotations

import tempfile
from collections.abc import Callable
from pathlib import Path

import structlog

from app.installer.models import InstallerManifest
from app.installer.steps import STEP_HANDLERS, StepError

logger = structlog.get_logger(__name__)


class InstallExecutor:
    """Executes installer steps sequentially with progress reporting."""

    def __init__(self, manifest: InstallerManifest, game_dir: str) -> None:
        self.manifest = manifest
        self.game_dir = Path(game_dir)
        self.temp_dir: Path | None = None
        self._cancelled = False

    async def execute(
        self,
        on_progress: Callable[[int, int, str, str], None] | None = None,
    ) -> None:
        """Execute all steps in the installer manifest."""
        total_steps = len(self.manifest.steps)
        logger.info(
            "Starting installation",
            name=self.manifest.name,
            steps=total_steps,
            game_dir=str(self.game_dir),
        )

        # Create temp directory for downloads
        with tempfile.TemporaryDirectory(prefix="newheroic_") as tmp:
            self.temp_dir = Path(tmp)

            # Create game directory
            self.game_dir.mkdir(parents=True, exist_ok=True)

            for i, step in enumerate(self.manifest.steps):
                if self._cancelled:
                    logger.warning("Installation cancelled")
                    return

                logger.info(
                    "Executing step",
                    step=i + 1,
                    total=total_steps,
                    action=step.action,
                )

                if on_progress:
                    on_progress(i, total_steps, step.action, step.description)

                handler = STEP_HANDLERS.get(step.action)
                if handler is None:
                    logger.warning(
                        "Unknown step action, skipping",
                        action=step.action,
                    )
                    continue

                try:
                    await handler(step.config, self.game_dir, self.temp_dir)
                except StepError:
                    logger.error(
                        "Step failed",
                        step=i + 1,
                        action=step.action,
                    )
                    raise
                except FileNotFoundError as e:
                    logger.error(
                        "Required tool not found for step",
                        step=i + 1,
                        error=str(e),
                    )
                    raise StepError(f"Required tool not found: {e}") from e

        logger.info("Installation complete", name=self.manifest.name)

    def cancel(self) -> None:
        """Cancel the running installation."""
        self._cancelled = True
        logger.info("Cancellation requested", name=self.manifest.name)
