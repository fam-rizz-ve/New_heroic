"""Background sync manager for store game libraries."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from typing import Any

import structlog

from app.stores.manager import StoreManager

logger = structlog.get_logger(__name__)


@dataclass
class SyncState:
    """State of a background sync task."""

    task_id: str
    store_name: str
    status: str = "running"
    progress: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


_tasks: dict[str, SyncState] = {}


async def _do_sync(store_name: str, state: SyncState) -> None:
    """Run the actual sync in background."""
    logger.info("Background sync started", store=store_name)

    try:
        manager = StoreManager.create_default()
        store = manager.get(store_name)
        if store is None:
            state.status = "failed"
            state.error = f"Store '{store_name}' not found"
            return

        from app.api.dependencies import get_use_cases

        use_cases = get_use_cases()

        state.progress = {"store": store_name}
        store_games = await store.list_games()
        total = len(store_games)
        state.progress = {"store": store_name, "current": 0, "total": total}

        libraries = use_cases._library_repo.list_all()
        if not libraries:
            state.status = "failed"
            state.error = "Default library not initialized"
            return
        library = libraries[0]

        imported = 0
        errors: list[str] = []

        from app.core.domain.enums import RunnerType, StoreSource
        from app.core.domain.game import Game as DomainGame
        from app.core.domain.library import DuplicateGameError
        from app.core.domain.value_objects import GameId, GameTitle

        # Build set of (store, title_lower) for O(1) dedup across syncs
        existing: set[tuple[str, str]] = set()
        for g in library.games.values():
            existing.add((g.store.value, g.title.value.lower()))

        for i, sg in enumerate(store_games):
            try:
                # Skip if already exists (by store + title)
                key = (store_name, sg.title.lower())
                if key in existing:
                    continue

                title = GameTitle(sg.title)
                domain_game = DomainGame(
                    id=GameId.generate(),
                    title=title,
                    store=StoreSource(store_name),
                    runner=RunnerType.WINE,
                    description=sg.description,
                    cover_art_url=sg.cover_art_url,
                )
                library.add_game(domain_game)
                use_cases._game_repo.save(domain_game)
                imported += 1
                existing.add(key)
            except DuplicateGameError:
                pass
            except Exception as e:
                errors.append(f"{sg.title}: {e}")

            if i % 10 == 0:
                state.progress = {
                    "store": store_name,
                    "current": i + 1,
                    "total": total,
                }
                await asyncio.sleep(0)

        use_cases._library_repo.save(library)

        # After sync, try to fetch covers for any games that lack them
        try:
            from app.stores.cover_service import refresh_missing_covers

            cover_result = await refresh_missing_covers()
            if cover_result["refreshed"] > 0:
                logger.info(
                    "Auto-refreshed missing covers after sync",
                    count=cover_result["refreshed"],
                )
        except Exception as e:
            logger.warning("Cover refresh after sync failed", error=str(e))

        state.status = "completed"
        state.result = {
            "imported": imported,
            "errors": errors,
            "total": total,
            "store": store_name,
        }
        logger.info(
            "Background sync completed",
            store=store_name,
            imported=imported,
            total=total,
        )

    except Exception as e:
        state.status = "failed"
        state.error = str(e)
        logger.error("Background sync failed", store=store_name, error=str(e))


def start_sync(store_name: str) -> str:
    """Start a background sync task.

    Args:
        store_name: Name of the store to sync.

    Returns:
        Task ID string for status polling.
    """
    task_id = str(uuid.uuid4())
    state = SyncState(task_id=task_id, store_name=store_name)
    _tasks[task_id] = state

    asyncio.create_task(_do_sync(store_name, state))

    logger.info("Sync task created", task_id=task_id, store=store_name)
    return task_id


def get_sync_status(task_id: str) -> dict[str, Any] | None:
    """Get the status of a background sync task.

    Args:
        task_id: The task ID from start_sync().

    Returns:
        Dict with status info, or None if task_id not found.
    """
    state = _tasks.get(task_id)
    if state is None:
        return None

    result: dict[str, Any] = {"status": state.status, "store": state.store_name}
    if state.progress:
        result["progress"] = state.progress
    if state.result:
        result["result"] = state.result
    if state.error:
        result["error"] = state.error

    return result
