"""Background sync API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.sync.manager import get_sync_status, start_sync

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("/{store_name}")
async def trigger_sync(store_name: str) -> dict[str, str]:
    """Start a background sync for the given store.

    Returns immediately with a task_id for status polling.
    """
    task_id = start_sync(store_name)
    return {"task_id": task_id, "store": store_name, "status": "started"}


@router.get("/{task_id}")
async def sync_status(task_id: str) -> dict[str, Any]:
    """Get the status of a background sync task."""
    status = get_sync_status(task_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return status
