"""Service for auto-downloading missing game cover art."""

from __future__ import annotations

import asyncio

import httpx
import structlog

from app.core.interfaces.repositories import GameRepository
from app.core.use_cases.library import GameResult, LibraryUseCases

logger = structlog.get_logger(__name__)

STEAM_SEARCH_URL = "https://store.steampowered.com/api/storesearch"
STEAM_COVER_CDN = "https://steamcdn-a.akamaihd.net/steam/apps/{appid}/library_600x900.jpg"


async def search_steam_cover(game_title: str) -> str | None:
    """Search for a game cover on the Steam store by title.

    Uses the Steam store search API (free, no key required).
    Returns the cover URL string if found, None otherwise.
    """
    if not game_title or not game_title.strip():
        return None

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                STEAM_SEARCH_URL,
                params={"term": game_title.strip(), "l": "en", "cc": "US"},
            )
            resp.raise_for_status()
            data = resp.json()

            items = data.get("items", [])
            if not items:
                logger.debug("No Steam search results", title=game_title)
                return None

            # Try exact name match first
            title_lower = game_title.strip().lower()
            for item in items:
                item_name = item.get("name", "").lower()
                if item_name == title_lower:
                    appid = item.get("id")
                    if appid:
                        cover_url = STEAM_COVER_CDN.format(appid=appid)
                        logger.info("Found exact cover match", title=game_title, appid=appid)
                        return cover_url

            # Fall back to first result
            first = items[0]
            appid = first.get("id")
            if appid:
                cover_url = STEAM_COVER_CDN.format(appid=appid)
                logger.info(
                    "Found approximate cover match",
                    title=game_title,
                    matched=first.get("name"),
                    appid=appid,
                )
                return cover_url

    except httpx.TimeoutException:
        logger.warning("Steam search timed out", title=game_title)
    except httpx.HTTPStatusError as e:
        logger.warning("Steam search HTTP error", title=game_title, status=e.response.status_code)
    except httpx.RequestError as e:
        logger.warning("Steam search request failed", title=game_title, error=str(e))
    except Exception as e:
        logger.error("Steam search failed unexpectedly", title=game_title, error=str(e))

    return None


async def refresh_game_cover(
    game_id: str,
    repo: GameRepository | None = None,
    use_cases: LibraryUseCases | None = None,
) -> bool:
    """Try to find and update a cover for a specific game.

    Accepts optional repo and use_cases to allow callers to inject dependencies.
    Falls back to importing from api if not provided.

    Returns True if cover was found and updated, False otherwise.
    """
    if use_cases is None:
        from app.api.dependencies import get_use_cases as _get_uc
        use_cases = _get_uc()
    if repo is None:
        from app.api.dependencies import get_game_repo as _get_repo
        repo = _get_repo()

    from app.core.domain.value_objects import GameId as DomainGameId

    try:
        gid = DomainGameId.from_str(game_id)
    except (ValueError, TypeError):
        logger.warning("Invalid game ID for cover refresh", game_id=game_id)
        return False

    game = use_cases.get_game(gid)
    if game is None:
        logger.warning("Game not found for cover refresh", game_id=game_id)
        return False

    # Skip if already has cover
    if game.cover_art_url:
        logger.debug("Game already has cover, skipping", title=game.title)
        return False

    cover_url = await search_steam_cover(game.title)
    if cover_url:
        try:
            domain_game = repo.get(gid)
            if domain_game:
                domain_game.set_cover_art(cover_url)
                repo.save(domain_game)
                logger.info("Cover updated successfully", title=game.title, game_id=game_id)
                return True
        except Exception as e:
            logger.error("Failed to save cover", title=game.title, error=str(e))

    return False


async def refresh_missing_covers(
    repo: GameRepository | None = None,
    use_cases: LibraryUseCases | None = None,
) -> dict[str, int]:
    """Batch refresh all games that don't have cover art.

    Uses asyncio.gather with a Semaphore(10) for concurrent Steam API calls.

    Returns dict with 'refreshed' and 'failed' counts.
    """
    if use_cases is None:
        from app.api.dependencies import get_use_cases as _get_uc
        use_cases = _get_uc()
    if repo is None:
        from app.api.dependencies import get_game_repo as _get_repo
        repo = _get_repo()

    all_games = use_cases.list_all_games()
    missing = [g for g in all_games if not g.cover_art_url]

    if not missing:
        return {"refreshed": 0, "failed": 0, "total_checked": 0}

    semaphore = asyncio.Semaphore(10)

    async def _refresh_one(game: GameResult) -> bool:
        async with semaphore:
            return await refresh_game_cover(game.id, repo=repo, use_cases=use_cases)

    results = await asyncio.gather(*[_refresh_one(g) for g in missing], return_exceptions=True)
    refreshed = sum(1 for r in results if r is True)
    failed = sum(1 for r in results if r is not True)

    logger.info(
        "Cover refresh complete",
        refreshed=refreshed,
        failed=failed,
        total_checked=len(missing),
    )

    return {"refreshed": refreshed, "failed": failed, "total_checked": len(missing)}
