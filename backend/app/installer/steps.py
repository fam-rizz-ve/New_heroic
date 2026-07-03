"""Individual step handlers for the installer engine."""

from __future__ import annotations

import asyncio
import stat
from collections.abc import Callable
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class StepError(Exception):
    """Raised when an installer step fails."""

    pass


async def handle_download(config: dict[str, Any], game_dir: Path, temp_dir: Path) -> None:
    """Download a file from a URL."""
    url = config.get("url", config.get("src", ""))
    dest = config.get("dst", temp_dir) if isinstance(config.get("dst"), str) else temp_dir
    filename = config.get("file", url.split("/")[-1] if url else "download")

    if not url:
        raise StepError("Download step requires a 'url' or 'src' config value")

    dest_path = Path(dest) / filename
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Downloading file", url=url, dest=str(dest_path))

    proc = await asyncio.create_subprocess_exec(
        "curl",
        "-L",
        "-o",
        str(dest_path),
        url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise StepError(f"Download failed: {stderr.decode().strip()}")

    logger.info("Download complete", path=str(dest_path), size=dest_path.stat().st_size)


async def handle_extract(config: dict[str, Any], game_dir: Path, temp_dir: Path) -> None:
    """Extract an archive file."""
    src = config.get("file", config.get("src", ""))
    dst = Path(str(config.get("dst", str(game_dir))))

    if not src:
        raise StepError("Extract step requires a 'file' or 'src' config value")

    src_path = Path(src)
    if not src_path.is_absolute():
        src_path = temp_dir / src_path

    if not src_path.exists():
        raise StepError(f"File not found: {src_path}")

    dst.mkdir(parents=True, exist_ok=True)

    logger.info("Extracting archive", src=str(src_path), dst=str(dst))

    ext = src_path.suffix.lower()
    if ext in (".zip",):
        proc = await asyncio.create_subprocess_exec(
            "unzip",
            "-o",
            str(src_path),
            "-d",
            str(dst),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    elif ext in (".tar", ".gz", ".bz2", ".xz"):
        proc = await asyncio.create_subprocess_exec(
            "tar",
            "-xf",
            str(src_path),
            "-C",
            str(dst),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    else:
        raise StepError(f"Unsupported archive format: {ext}")

    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise StepError(f"Extraction failed: {stderr.decode().strip()}")

    logger.info("Extraction complete")


async def handle_execute(config: dict[str, Any], game_dir: Path, temp_dir: Path) -> None:
    """Execute a shell command."""
    command = config.get("command", config.get("value", ""))

    if not command:
        raise StepError("Execute step requires a 'command' config value")

    logger.info("Executing command", command=command)

    proc = await asyncio.create_subprocess_exec(
        "sh",
        "-c",
        command,
        cwd=str(game_dir),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        logger.error(
            "Command failed",
            command=command,
            stderr=stderr.decode().strip(),
        )
        raise StepError(
            f"Command failed (exit {proc.returncode}): {stderr.decode().strip()}"
        )

    if stdout:
        logger.debug("Command output", output=stdout.decode().strip())


async def handle_mkdir(config: dict[str, Any], game_dir: Path, temp_dir: Path) -> None:
    """Create a directory."""
    path = config.get("path", config.get("value", ""))

    if not path:
        raise StepError("Mkdir step requires a 'path' config value")

    dir_path = Path(path)
    if not dir_path.is_absolute():
        dir_path = game_dir / dir_path
    dir_path.mkdir(parents=True, exist_ok=True)
    logger.info("Directory created", path=str(dir_path))


async def handle_chmodx(config: dict[str, Any], game_dir: Path, temp_dir: Path) -> None:
    """Make a file executable."""
    path = config.get("path", config.get("value", config.get("file", "")))

    if not path:
        raise StepError("Chmodx step requires a 'path', 'value', or 'file' config")

    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = game_dir / file_path

    if not file_path.exists():
        raise StepError(f"File not found: {file_path}")

    file_path.chmod(file_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    logger.info("File made executable", path=str(file_path))


async def handle_require(config: dict[str, Any], game_dir: Path, temp_dir: Path) -> None:
    """Check that a requirement is met (runner, tool, etc.)."""
    requirement = config.get("value", config.get("name", ""))

    if not requirement:
        raise StepError("Require step needs a 'value' or 'name' config")

    # Check if executable exists
    proc = await asyncio.create_subprocess_exec(
        "which",
        requirement,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate()

    if proc.returncode != 0:
        raise StepError(
            f"Required dependency not found: '{requirement}'. "
            f"Please install it and try again."
        )

    logger.info("Requirement satisfied", requirement=requirement)


# Map action names to handler functions
STEP_HANDLERS: dict[str, Callable[..., Any]] = {
    "download": handle_download,
    "extract": handle_extract,
    "execute": handle_execute,
    "mkdir": handle_mkdir,
    "chmodx": handle_chmodx,
    "require": handle_require,
}
