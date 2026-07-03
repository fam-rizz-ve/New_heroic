"""API endpoints for Wine/Proton version management."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.runners.wine_manager import WineManager
from app.schemas.wine import (
    WineDownloadProgress,
    WineInstallRequest,
    WineVersionResponse,
)

router = APIRouter(prefix="/wine", tags=["wine"])

# Module-level singleton; replaced with DI wiring in production.
_manager: WineManager | None = None


def get_wine_manager() -> WineManager:
    """Dependency: get the WineManager singleton."""
    global _manager
    if _manager is None:
        _manager = WineManager()
    return _manager


@router.get("/versions", response_model=list[WineVersionResponse])
async def list_available_versions(
    source: str = "all",
    manager: WineManager = Depends(get_wine_manager),
) -> list[WineVersionResponse]:
    """List available Wine/Proton versions from GitHub releases.

    Args:
        source: Filter by source ("wine-ge", "proton-ge", "lutris-wine", or "all").

    Returns:
        A list of WineVersionResponse with available releases.
    """
    versions = await manager.list_available_versions(source=source)
    return [
        WineVersionResponse(
            name=v.name,
            version=v.version,
            source=v.source,
            url=v.url,
            filename=v.filename,
            release_date=v.release_date,
            is_installed=v.is_installed,
            install_path=v.install_path,
        )
        for v in versions
    ]


@router.get("/installed", response_model=list[WineVersionResponse])
async def list_installed_versions(
    manager: WineManager = Depends(get_wine_manager),
) -> list[WineVersionResponse]:
    """List installed Wine/Proton versions.

    Returns:
        A list of WineVersionResponse for locally installed versions.
    """
    versions = manager.list_installed_versions()
    return [
        WineVersionResponse(
            name=v.name,
            version=v.version,
            source=v.source,
            url=v.url,
            filename=v.filename,
            release_date=v.release_date,
            is_installed=v.is_installed,
            install_path=v.install_path,
        )
        for v in versions
    ]


@router.post("/install", response_model=dict[str, str])
async def install_version(
    request: WineInstallRequest,
    manager: WineManager = Depends(get_wine_manager),
) -> dict[str, str]:
    """Download and install a Wine/Proton version.

    Args:
        request: WineInstallRequest with version_name and version_url.

    Returns:
        A dict with "path" indicating the install directory.

    Raises:
        HTTPException 500: If the download or extraction fails.
    """
    try:
        install_path = await manager.download_version(
            request.version_name,
            request.version_url,
        )
        return {"path": install_path}
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/downloads/{version_name}",
    response_model=WineDownloadProgress | None,
)
async def get_download_progress(
    version_name: str,
    manager: WineManager = Depends(get_wine_manager),
) -> dict[str, Any] | None:
    """Get download progress for a specific version.

    Args:
        version_name: The version name to query.

    Returns:
        WineDownloadProgress dict, or None if no download is tracked.
    """
    return manager.get_download_progress(version_name)


@router.delete("/versions/{version_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_version(
    version_name: str,
    manager: WineManager = Depends(get_wine_manager),
) -> None:
    """Delete an installed Wine/Proton version.

    Args:
        version_name: The name of the version to delete.

    Raises:
        HTTPException 404: If the version is not installed.
        HTTPException 500: If the deletion fails.
    """
    try:
        await manager.delete_version(version_name)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except OSError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
