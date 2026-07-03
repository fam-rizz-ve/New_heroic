"""Proton runner — runs Windows games via Steam Proton."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from app.runners.base import RunnerBase, RunnerInfo


class ProtonRunner(RunnerBase):
    """Runner for Windows games using Steam Proton."""

    name = "proton"
    display_name = "Proton (Steam)"
    _proton_binary: str | None = None
    _proton_version: str = ""

    async def detect(self) -> RunnerInfo:
        """Detect Proton installation from Steam directories."""
        self.logger.info("Detecting Proton installation")

        # Common Steam compatibility tool directories
        steam_paths = [
            os.path.expanduser("~/.steam/steam"),
            os.path.expanduser("~/.local/share/Steam"),
            os.path.expanduser("~/.var/app/com.valvesoftware.Steam/data/Steam"),
        ]

        proton_paths: list[str] = []
        for steam_path in steam_paths:
            compat_tools = os.path.join(steam_path, "compatibilitytools.d")
            if os.path.isdir(compat_tools):
                for item in os.listdir(compat_tools):
                    if "proton" in item.lower():
                        proton_bin = os.path.join(compat_tools, item, "proton")
                        if os.path.isfile(proton_bin):
                            proton_paths.append(proton_bin)

        if not proton_paths:
            self.logger.info("No Proton installations found")
            return RunnerInfo(
                name=self.name,
                display_name=self.display_name,
                version="",
                path=None,
                is_installed=False,
            )

        # Use the first Proton found
        self._proton_binary = proton_paths[0]

        # Get version from directory name or run proton --version
        dir_name = os.path.basename(os.path.dirname(self._proton_binary))
        try:
            ver_proc = await asyncio.create_subprocess_exec(
                self._proton_binary, "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await ver_proc.communicate()
            self._proton_version = stdout.decode().strip() or dir_name
        except Exception:
            self._proton_version = dir_name

        self.logger.info(
            "Proton detected",
            version=self._proton_version,
            path=self._proton_binary,
        )

        return RunnerInfo(
            name=self.name,
            display_name=self.display_name,
            version=self._proton_version,
            path=self._proton_binary,
            is_installed=True,
        )

    async def run_game(
        self,
        executable: str,
        args: list[str] | None = None,
        env_vars: dict[str, str] | None = None,
    ) -> None:
        """Launch a Windows game with Proton."""
        if not self._proton_binary:
            raise RuntimeError("Proton is not installed")

        cmd = [self._proton_binary, "run", executable]
        if args:
            cmd.extend(args)

        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        self.logger.info(
            "Launching game with Proton",
            executable=executable,
            proton_binary=self._proton_binary,
        )

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self.logger.info("Proton game process started", pid=proc.pid)

    async def get_settings(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "version": self._proton_version,
            "binary": self._proton_binary,
            "proton_path": os.path.dirname(self._proton_binary) if self._proton_binary else None,
        }

    async def set_setting(self, key: str, value: str) -> None:
        self.logger.warning("Proton settings not fully implemented", key=key)
