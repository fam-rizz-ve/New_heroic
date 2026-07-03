"""Native runner — executes games directly on the system."""

from __future__ import annotations

import os
from typing import Any

from app.runners.base import RunnerBase, RunnerInfo


class NativeRunner(RunnerBase):
    """Runner that executes games natively on the system."""

    name = "native"
    display_name = "Native"

    async def detect(self) -> RunnerInfo:
        """Native runner is always available on Linux."""
        self.logger.info("Native runner detected")
        return RunnerInfo(
            name=self.name,
            display_name=self.display_name,
            version="1.0",
            is_installed=True,
        )

    async def run_game(
        self,
        executable: str,
        args: list[str] | None = None,
        env_vars: dict[str, str] | None = None,
    ) -> None:
        """Run a native executable directly."""
        import asyncio

        cmd = [executable]
        if args:
            cmd.extend(args)

        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        self.logger.info("Launching native game", executable=executable)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Detach - don't wait for completion for game processes
        self.logger.info("Native game process started", pid=proc.pid)

    async def get_settings(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "executable_direct": True,
        }

    async def set_setting(self, key: str, value: str) -> None:
        self.logger.debug("Setting not applicable for native runner", key=key)
