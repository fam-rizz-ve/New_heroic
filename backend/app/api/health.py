"""Health check endpoint for verifying IPC connectivity."""

import structlog
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.config import Settings

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/health")
@inject
async def health(
    config: Settings = Depends(Provide["config"]),
) -> dict[str, str]:
    """Return the current health status of the backend.

    Used by the frontend to verify IPC connectivity.
    """
    logger.info("health_check_requested")
    return {
        "status": "ok",
        "version": config.app_version,
        "app_name": config.app_name,
    }
