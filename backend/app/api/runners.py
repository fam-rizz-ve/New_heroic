"""API endpoints for runner management."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.runners.manager import RunnerManager

router = APIRouter(prefix="/runners", tags=["runners"])

_runner_manager: RunnerManager | None = None


def get_runner_manager() -> RunnerManager:
    """Dependency: get the runner manager singleton."""
    global _runner_manager
    if _runner_manager is None:
        _runner_manager = RunnerManager.create_default()
    return _runner_manager


@router.get("")
async def list_runners(
    manager: RunnerManager = Depends(get_runner_manager),
) -> list[dict[str, Any]]:
    """List all available runners."""
    return manager.list_available()


@router.get("/detect")
async def detect_runners(
    manager: RunnerManager = Depends(get_runner_manager),
) -> list[dict[str, Any]]:
    """Detect all runners and return their installation status."""
    results = await manager.detect_all()
    return results


@router.get("/{runner_name}/detect")
async def detect_runner(
    runner_name: str,
    manager: RunnerManager = Depends(get_runner_manager),
) -> dict[str, Any]:
    """Detect a specific runner."""
    runner = manager.get(runner_name)
    if runner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Runner '{runner_name}' not found",
        )
    try:
        info = await runner.detect()
        return {
            "name": info.name,
            "display_name": runner.display_name,
            "version": info.version,
            "path": info.path,
            "is_installed": info.is_installed,
            "config": info.config,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
