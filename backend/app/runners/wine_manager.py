"""Wine/Proton version download and management.

Downloads and manages Wine-GE / Proton-GE versions from
GloriousEggroll releases, and Lutris Wine builds.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import time
from dataclasses import dataclass
from typing import Any

import structlog

TOOLS_DIR = os.path.expanduser("~/.config/new_heroic/tools")
WINE_GE_RELEASES = (
    "https://api.github.com/repos/GloriousEggroll/wine-ge-custom/releases"
)
PROTON_GE_RELEASES = (
    "https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases"
)
LUTRIS_WINE_RELEASES = (
    "https://api.github.com/repos/lutris/wine/releases"
)


@dataclass
class WineVersion:
    """Represents a downloadable Wine/Proton version."""

    name: str
    version: str
    source: str  # "wine-ge", "proton-ge", "lutris-wine"
    url: str | None
    filename: str | None
    release_date: str | None = None
    is_installed: bool = False
    install_path: str | None = None


def _parse_version_from_tag(tag_name: str, source: str) -> str:
    """Extract a human-readable version string from a GitHub release tag.

    Args:
        tag_name: The GitHub release tag (e.g., "wine-ge-8-25").
        source: The source prefix ("wine-ge", "proton-ge", "lutris-wine").

    Returns:
        A cleaned version string (e.g., "GE-Proton8-25").
    """
    if source == "proton-ge":
        # Tag like "GE-Proton8-25" or "proton-ge-8-25"
        cleaned = tag_name
        if cleaned.startswith("proton-ge-"):
            parts = cleaned.replace("proton-ge-", "", 1).split("-")
            return f"GE-Proton{'-'.join(parts)}"
        return cleaned
    if source == "lutris-wine":
        return tag_name.replace("lutris-wine-", "Lutris-Wine-", 1)
    # wine-ge: tag like "wine-ge-8-25" -> "Wine-GE-8-25"
    return tag_name.replace("wine-ge-", "Wine-GE-", 1)


class WineManager:
    """Download and manage Wine/Proton versions.

    Fetches available releases from GitHub API, tracks download
    progress, and manages local installations.
    """

    def __init__(self) -> None:
        self.logger = structlog.get_logger("app.runners.WineManager")
        self._download_progress: dict[str, dict[str, Any]] = {}
        os.makedirs(TOOLS_DIR, exist_ok=True)

    async def list_available_versions(self, source: str = "all") -> list[WineVersion]:
        """Fetch available Wine/Proton versions from GitHub releases.

        Args:
            source: Filter by source — "wine-ge", "proton-ge",
                    "lutris-wine", or "all" (default).

        Returns:
            A list of WineVersion objects with available releases.
        """
        installed = self.list_installed_versions()
        installed_names = {v.name for v in installed}

        sources_to_fetch: list[tuple[str, str]] = []
        if source in ("all", "wine-ge"):
            sources_to_fetch.append(("wine-ge", WINE_GE_RELEASES))
        if source in ("all", "proton-ge"):
            sources_to_fetch.append(("proton-ge", PROTON_GE_RELEASES))
        if source in ("all", "lutris-wine"):
            sources_to_fetch.append(("lutris-wine", LUTRIS_WINE_RELEASES))

        versions: list[WineVersion] = []
        for src, api_url in sources_to_fetch:
            try:
                batch = await self._fetch_releases(src, api_url, installed_names)
                versions.extend(batch)
            except Exception:
                self.logger.exception(
                    "Failed to fetch releases",
                    source=src,
                )
        return versions

    async def _fetch_releases(
        self,
        source: str,
        api_url: str,
        installed_names: set[str],
    ) -> list[WineVersion]:
        """Fetch and parse releases from a GitHub API URL.

        Args:
            source: The source identifier.
            api_url: The GitHub releases API URL.
            installed_names: Set of already-installed version names.

        Returns:
            A list of WineVersion objects parsed from the response.

        Raises:
            RuntimeError: If the HTTP request fails.
        """
        self.logger.debug("Fetching releases", source=source, url=api_url)

        proc = await asyncio.create_subprocess_exec(
            "curl",
            "-s",
            "-L",
            api_url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(
                f"Failed to fetch {source} releases: {stderr.decode().strip()}"
            )

        releases = json.loads(stdout)
        if not isinstance(releases, list):
            self.logger.warning(
                "Unexpected API response format",
                source=source,
            )
            return []

        versions: list[WineVersion] = []
        for release in releases:
            tag_name = release.get("tag_name", "")
            version_str = _parse_version_from_tag(tag_name, source)
            release_date = release.get("published_at")

            # Find a .tar.gz, .tar.xz, or .tar.zst asset
            assets = release.get("assets", [])
            asset_url: str | None = None
            asset_name: str | None = None
            for asset in assets:
                name: str = asset.get("name", "")
                if name.endswith((".tar.gz", ".tar.xz", ".tar.zst")):
                    asset_url = asset.get("browser_download_url")
                    asset_name = name
                    break

            is_installed = version_str in installed_names
            install_path: str | None = None
            if is_installed:
                install_path = os.path.join(TOOLS_DIR, version_str)

            versions.append(WineVersion(
                name=version_str,
                version=version_str,
                source=source,
                url=asset_url,
                filename=asset_name,
                release_date=release_date,
                is_installed=is_installed,
                install_path=install_path,
            ))

        return versions

    def list_installed_versions(self) -> list[WineVersion]:
        """List locally installed Wine/Proton versions.

        Scans TOOLS_DIR for directories matching known naming
        patterns for Wine-GE, Proton-GE, and Lutris-Wine builds.

        Returns:
            A list of WineVersion objects for installed versions.
        """
        if not os.path.isdir(TOOLS_DIR):
            return []

        versions: list[WineVersion] = []
        try:
            entries = os.listdir(TOOLS_DIR)
        except OSError:
            self.logger.exception("Failed to list tools directory")
            return []

        for entry in entries:
            full_path = os.path.join(TOOLS_DIR, entry)
            if not os.path.isdir(full_path):
                continue

            source: str | None = None
            if entry.startswith("Wine-GE-"):
                source = "wine-ge"
            elif entry.startswith("GE-Proton"):
                source = "proton-ge"
            elif entry.startswith("Lutris-Wine-"):
                source = "lutris-wine"

            if source is None:
                continue

            versions.append(WineVersion(
                name=entry,
                version=entry,
                source=source,
                url=None,
                filename=None,
                is_installed=True,
                install_path=full_path,
            ))

        self.logger.debug(
            "Scanned installed versions",
            count=len(versions),
        )
        return versions

    async def download_version(self, version_name: str, version_url: str) -> str:
        """Download and extract a Wine/Proton version.

        Downloads the archive from the given URL and extracts it
        into TOOLS_DIR/{version_name}. Tracks download progress
        for the frontend.

        Args:
            version_name: The name to store the version under.
            version_url: The URL of the archive to download.

        Returns:
            The install path of the extracted version.

        Raises:
            RuntimeError: If the download or extraction fails.
        """
        install_dir = os.path.join(TOOLS_DIR, version_name)
        archive_path = os.path.join(TOOLS_DIR, f"{version_name}.tmp")

        if os.path.isdir(install_dir):
            self.logger.info(
                "Version already installed",
                version=version_name,
            )
            return install_dir

        os.makedirs(TOOLS_DIR, exist_ok=True)

        total_bytes = await self._get_content_length(version_url)
        total_mb = (total_bytes / 1_048_576) if total_bytes else 0.0

        self._download_progress[version_name] = {
            "percentage": 0.0,
            "speed_mbps": 0.0,
            "downloaded_mb": 0.0,
            "total_mb": total_mb,
            "status": "downloading",
        }

        try:
            self.logger.info(
                "Downloading version",
                version=version_name,
                url=version_url,
            )

            start_time = time.monotonic()
            proc = await asyncio.create_subprocess_exec(
                "curl",
                "-s",
                "-L",
                "-o",
                archive_path,
                version_url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Read curl output in a background task to approximate progress
            async def _track_progress() -> None:
                """Poll for download progress (approximate via file size)."""
                if not os.path.exists(archive_path):
                    return
                try:
                    last_size = 0
                    while True:
                        await asyncio.sleep(0.5)
                        if proc.returncode is not None:
                            break
                        try:
                            current_size = os.path.getsize(archive_path)
                            downloaded_mb = current_size / 1_048_576
                            elapsed = time.monotonic() - start_time
                            if elapsed > 0 and total_mb > 0:
                                speed_bps = (current_size - last_size) / 0.5
                                pct = (downloaded_mb / total_mb) * 100.0
                                self._download_progress[version_name].update({
                                    "percentage": round(min(pct, 100.0), 2),
                                    "speed_mbps": round(speed_bps / 1_048_576, 2),
                                    "downloaded_mb": round(downloaded_mb, 2),
                                })
                            last_size = current_size
                        except OSError:
                            break
                except Exception:
                    self.logger.debug("Progress tracking ended", version=version_name)

            progress_task = asyncio.create_task(_track_progress())
            stdout, stderr = await proc.communicate()
            progress_task.cancel()

            if proc.returncode != 0:
                raise RuntimeError(
                    f"Download failed (exit {proc.returncode}): {stderr.decode().strip()}"
                )

            self._download_progress[version_name]["status"] = "extracting"
            self._download_progress[version_name]["percentage"] = 75.0

            os.makedirs(install_dir, exist_ok=True)

            # Extract the archive
            extract_proc = await asyncio.create_subprocess_exec(
                "tar",
                "-xf",
                archive_path,
                "-C",
                install_dir,
                "--strip-components=1",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, extract_stderr = await extract_proc.communicate()

            if extract_proc.returncode != 0:
                shutil.rmtree(install_dir, ignore_errors=True)
                raise RuntimeError(
                    f"Extraction failed: {extract_stderr.decode().strip()}"
                )

            # Clean up archive
            os.remove(archive_path)

            self._download_progress[version_name].update({
                "percentage": 100.0,
                "status": "completed",
            })

            self.logger.info(
                "Version installed successfully",
                version=version_name,
                path=install_dir,
            )
            return install_dir

        except Exception:
            self._download_progress[version_name]["status"] = "failed"
            # Clean up partial files
            if os.path.exists(archive_path):
                os.remove(archive_path)
            if os.path.isdir(install_dir):
                shutil.rmtree(install_dir, ignore_errors=True)
            raise

    async def _get_content_length(self, url: str) -> int | None:
        """Get the Content-Length of a download URL via a HEAD request.

        Args:
            url: The URL to check.

        Returns:
            Content-Length in bytes, or None if it cannot be determined.
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                "curl", "-sI", "-L", url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            for line in stdout.decode().split("\n"):
                if line.lower().startswith("content-length:"):
                    return int(line.split(":", 1)[1].strip())
            self.logger.debug(
                "Content-Length header not found",
                url=url,
            )
        except Exception:
            self.logger.debug(
                "Failed to get content length",
                url=url,
                exc_info=True,
            )
        return None

    def get_download_progress(self, version_name: str) -> dict[str, Any] | None:
        """Get current download progress for a version.

        Args:
            version_name: The version name to query.

        Returns:
            A dict with percentage, speed_mbps, downloaded_mb, total_mb,
            and status keys, or None if no download is in progress.
        """
        return self._download_progress.get(version_name)

    async def delete_version(self, version_name: str) -> None:
        """Remove a downloaded Wine/Proton version.

        Args:
            version_name: The name of the version to delete.

        Raises:
            FileNotFoundError: If the version is not installed.
        """
        install_dir = os.path.join(TOOLS_DIR, version_name)
        if not os.path.isdir(install_dir):
            raise FileNotFoundError(
                f"Version '{version_name}' is not installed at {install_dir}"
            )

        self.logger.info(
            "Deleting version",
            version=version_name,
            path=install_dir,
        )
        shutil.rmtree(install_dir)
        self._download_progress.pop(version_name, None)
        self.logger.info(
            "Version deleted successfully",
            version=version_name,
        )
