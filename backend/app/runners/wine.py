"""Wine runner — runs Windows games via Wine/Wine64."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from app.runners.base import RunnerBase, RunnerInfo


class WineRunner(RunnerBase):
    """Runner for Windows games using Wine."""

    name = "wine"
    display_name = "Wine"
    _wine_binary: str | None = None
    _wine_version: str = ""

    async def detect(self) -> RunnerInfo:
        """Detect Wine installation on the system."""
        self.logger.info("Detecting Wine installation")

        for binary in ["wine64", "wine"]:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "which", binary,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
                if proc.returncode == 0:
                    self._wine_binary = binary
                    self.logger.info("Wine binary found", binary=binary)
                    break
            except FileNotFoundError:
                continue

        if not self._wine_binary:
            self.logger.warning("Wine not found on system")
            return RunnerInfo(
                name=self.name,
                display_name=self.display_name,
                version="",
                path=None,
                is_installed=False,
            )

        # Get Wine version
        try:
            ver_proc = await asyncio.create_subprocess_exec(
                self._wine_binary, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await ver_proc.communicate()
            self._wine_version = stdout.decode().strip()
        except Exception:
            self._wine_version = "unknown"

        self.logger.info("Wine detected", version=self._wine_version, binary=self._wine_binary)

        return RunnerInfo(
            name=self.name,
            display_name=self.display_name,
            version=self._wine_version,
            path=self._wine_binary,
            is_installed=True,
            config={
                "wine_prefix": os.environ.get("WINEPREFIX", os.path.expanduser("~/.wine")),
                "wine_arch": os.environ.get("WINEARCH", "win64"),
            },
        )

    async def run_game(
        self,
        executable: str,
        args: list[str] | None = None,
        env_vars: dict[str, str] | None = None,
    ) -> None:
        """Launch a Windows game with Wine."""
        if not self._wine_binary:
            raise RuntimeError("Wine is not installed or not found")

        cmd = [self._wine_binary, executable]
        if args:
            cmd.extend(args)

        env = os.environ.copy()
        env.setdefault("WINEPREFIX", os.path.expanduser("~/.wine"))
        if env_vars:
            env.update(env_vars)

        self.logger.info(
            "Launching game with Wine",
            executable=executable,
            wine_binary=self._wine_binary,
        )

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self.logger.info("Wine game process started", pid=proc.pid)

    async def get_settings(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "version": self._wine_version,
            "binary": self._wine_binary,
            "wine_prefix": os.environ.get("WINEPREFIX", os.path.expanduser("~/.wine")),
            "wine_arch": os.environ.get("WINEARCH", "win64"),
        }

    async def set_setting(self, key: str, value: str) -> None:
        """Set a Wine configuration value via environment variable or config file."""
        allowed_keys = ["wine_prefix", "wine_arch"]
        if key not in allowed_keys:
            self.logger.warning("Unknown Wine setting", key=key, allowed=allowed_keys)
            return
        os.environ[key.upper()] = value
        self.logger.info("Wine setting updated", key=key, value=value)
