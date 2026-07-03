"""Tests for WineManager (mocked GitHub API)."""

from __future__ import annotations

import json
import os
from unittest.mock import AsyncMock, patch

import pytest

from app.runners.wine_manager import (
    TOOLS_DIR,
    WineManager,
    _parse_version_from_tag,
)


class TestVersionParsing:
    """Tests for the version tag parser."""

    def test_parse_wine_ge(self) -> None:
        """Parse a wine-ge tag correctly."""
        result = _parse_version_from_tag("wine-ge-8-25", "wine-ge")
        assert result == "Wine-GE-8-25"

    def test_parse_proton_ge_with_ge_prefix(self) -> None:
        """Parse a proton-ge tag with GE-Proton prefix."""
        result = _parse_version_from_tag("GE-Proton8-25", "proton-ge")
        assert result == "GE-Proton8-25"

    def test_parse_proton_ge_with_proton_prefix(self) -> None:
        """Parse a proton-ge tag with proton-ge prefix."""
        result = _parse_version_from_tag("proton-ge-8-25", "proton-ge")
        assert result == "GE-Proton8-25"

    def test_parse_lutris_wine(self) -> None:
        """Parse a lutris-wine tag."""
        result = _parse_version_from_tag("lutris-wine-8.0", "lutris-wine")
        assert result == "Lutris-Wine-8.0"


class TestWineManagerListInstalled:
    """Tests for listing installed versions."""

    @pytest.fixture
    def manager(self) -> WineManager:
        """Create a WineManager instance."""
        return WineManager()

    def test_no_tools_dir(self, manager: WineManager, tmp_path: str) -> None:
        """When TOOLS_DIR does not exist, return empty list."""
        # Use a non-existent directory
        with patch.object(
            os.path,
            "isdir",
            return_value=False,
        ):
            versions = manager.list_installed_versions()
            assert versions == []

    @patch("os.listdir")
    @patch("os.path.isdir")
    def test_scan_directories(
        self,
        mock_isdir: AsyncMock,
        mock_listdir: AsyncMock,
        manager: WineManager,
    ) -> None:
        """Scan TOOLS_DIR and identify installed versions."""
        mock_listdir.return_value = [
            "Wine-GE-8-25",
            "GE-Proton8-25",
            "Lutris-Wine-8.0",
            "some_other_dir",
            "file.tar.gz",
        ]
        mock_isdir.side_effect = lambda p: True

        versions = manager.list_installed_versions()
        assert len(versions) == 3

        names = [v.name for v in versions]
        assert "Wine-GE-8-25" in names
        assert "GE-Proton8-25" in names
        assert "Lutris-Wine-8.0" in names

        sources = {v.name: v.source for v in versions}
        assert sources["Wine-GE-8-25"] == "wine-ge"
        assert sources["GE-Proton8-25"] == "proton-ge"
        assert sources["Lutris-Wine-8.0"] == "lutris-wine"


class TestWineManagerDownload:
    """Tests for downloading and deleting versions."""

    @pytest.fixture
    def manager(self) -> WineManager:
        """Create a WineManager instance with a temp TOOLS_DIR."""
        return WineManager()

    @patch("app.runners.wine_manager.WineManager.list_installed_versions")
    @patch("asyncio.create_subprocess_exec")
    async def test_list_available_versions(
        self,
        mock_subprocess: AsyncMock,
        mock_list_installed: AsyncMock,
        manager: WineManager,
    ) -> None:
        """Fetch available versions from mock GitHub API."""
        mock_list_installed.return_value = []

        mock_release_data = [
            {
                "tag_name": "wine-ge-8-25",
                "published_at": "2024-01-15T00:00:00Z",
                "assets": [
                    {
                        "name": "wine-ge-8-25-x86_64.tar.xz",
                        "browser_download_url": "https://example.com/wine-ge-8-25.tar.xz",
                    },
                ],
            },
            {
                "tag_name": "GE-Proton8-25",
                "published_at": "2024-02-01T00:00:00Z",
                "assets": [
                    {
                        "name": "GE-Proton8-25.tar.gz",
                        "browser_download_url": "https://example.com/GE-Proton8-25.tar.gz",
                    },
                ],
            },
        ]

        # Mock the curl subprocess for fetching JSON
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(
            return_value=(json.dumps(mock_release_data).encode(), b""),
        )
        mock_subprocess.return_value = mock_process

        versions = await manager.list_available_versions(source="all")

        # Should at least try to fetch wine-ge releases
        # Since we mock curl for wine-ge, it will succeed
        assert len(versions) >= 1
        # Check parsing
        wine_ge = [v for v in versions if v.source == "wine-ge"]
        if wine_ge:
            assert wine_ge[0].name == "Wine-GE-8-25"
            assert wine_ge[0].url == "https://example.com/wine-ge-8-25.tar.xz"

    @patch("os.makedirs")
    @patch("asyncio.create_subprocess_exec")
    async def test_download_version_already_installed(
        self,
        mock_subprocess: AsyncMock,
        mock_makedirs: AsyncMock,
        manager: WineManager,
    ) -> None:
        """Downloading an already-installed version returns the existing path."""
        version_name = "Wine-GE-8-25"
        install_dir = os.path.join(TOOLS_DIR, version_name)

        with patch.object(os.path, "isdir", return_value=True):
            result = await manager.download_version(
                version_name,
                "https://example.com/test.tar.xz",
            )
            assert result == install_dir
        mock_subprocess.assert_not_called()

    @patch("os.makedirs")
    @patch("shutil.rmtree")
    @patch("asyncio.create_subprocess_exec")
    async def test_delete_version_success(
        self,
        mock_subprocess: AsyncMock,
        mock_rmtree: AsyncMock,
        mock_makedirs: AsyncMock,
        manager: WineManager,
    ) -> None:
        """Delete an installed version removes the directory."""
        version_name = "Wine-GE-8-25"
        install_dir = os.path.join(TOOLS_DIR, version_name)

        with patch.object(os.path, "isdir", return_value=True):
            await manager.delete_version(version_name)
            mock_rmtree.assert_called_once_with(install_dir)

    @patch("os.makedirs")
    @patch("asyncio.create_subprocess_exec")
    async def test_delete_version_not_found(
        self,
        mock_subprocess: AsyncMock,
        mock_makedirs: AsyncMock,
        manager: WineManager,
    ) -> None:
        """Deleting a non-existent version raises FileNotFoundError."""
        with patch.object(os.path, "isdir", return_value=False):
            with pytest.raises(FileNotFoundError, match="not installed"):
                await manager.delete_version("nonexistent")


class TestWineManagerProgress:
    """Tests for download progress tracking."""

    @pytest.fixture
    def manager(self) -> WineManager:
        """Create a WineManager instance."""
        return WineManager()

    def test_get_progress_none(self, manager: WineManager) -> None:
        """Getting progress for an untracked version returns None."""
        assert manager.get_download_progress("nonexistent") is None

    def test_get_progress_tracked(self, manager: WineManager) -> None:
        """Getting progress for a tracked version returns the progress dict."""
        manager._download_progress["test-version"] = {
            "percentage": 50.0,
            "speed_mbps": 1.0,
            "downloaded_mb": 50.0,
            "total_mb": 100.0,
            "status": "downloading",
        }
        progress = manager.get_download_progress("test-version")
        assert progress is not None
        assert progress["percentage"] == 50.0
        assert progress["status"] == "downloading"
