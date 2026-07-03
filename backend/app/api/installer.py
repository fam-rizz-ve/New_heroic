"""API endpoints for game installation."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.installer.manager import InstallerManager
from app.schemas.installer import InstallStartRequest

router = APIRouter(prefix="/installer", tags=["installer"])

_installer_manager: InstallerManager | None = None


def get_installer_manager() -> InstallerManager:
    """Dependency: get the installer manager singleton."""
    global _installer_manager
    if _installer_manager is None:
        _installer_manager = InstallerManager()
    return _installer_manager


@router.post("/parse")
async def parse_installer_yaml(
    request: InstallStartRequest,
    manager: InstallerManager = Depends(get_installer_manager),
) -> dict[str, object]:
    """Parse an installer YAML and return its metadata."""
    try:
        manifest = manager.parse_installer(request.manifest_yaml)
        return {
            "name": manifest.name,
            "game_slug": manifest.game_slug,
            "version": manifest.version,
            "runner": manifest.runner,
            "year": manifest.year,
            "description": manifest.description,
            "steps": len(manifest.steps),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/install")
async def start_installation(
    request: InstallStartRequest,
    manager: InstallerManager = Depends(get_installer_manager),
) -> dict[str, object]:
    """Parse and run a game installer."""
    try:
        manifest = manager.parse_installer(request.manifest_yaml)
        await manager.run_installer(manifest, request.game_dir)
        return {
            "status": "completed",
            "game": manifest.name,
            "game_slug": manifest.game_slug,
            "game_dir": request.game_dir,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
