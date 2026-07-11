"""Service for auto-downloading missing game cover art."""

from __future__ import annotations

import asyncio
import json
import re
import urllib.parse
from typing import cast

import httpx
import structlog

from app.core.config import settings
from app.core.domain.enums import StoreSource
from app.core.interfaces.repositories import GameRepository
from app.core.use_cases.library import GameResult, LibraryUseCases

logger = structlog.get_logger(__name__)

STEAM_SEARCH_URL = "https://store.steampowered.com/api/storesearch"
STEAM_COVER_CDN = "https://steamcdn-a.akamaihd.net/steam/apps/{appid}/library_600x900.jpg"

STEAMGRIDDB_SEARCH_URL = "https://www.steamgriddb.com/api/v2/search/autocomplete/{query}"
STEAMGRIDDB_GRIDS_URL = "https://www.steamgriddb.com/api/v2/grids/game/{game_id}"

# GOG CDN patterns — the embed API returns small ~196x196 thumbnails from
# images.gog-cdn.com.  We try to "upscale" by requesting known larger
# size variants before falling back to other sources.
_GOG_CDN_RE = re.compile(
    r"https?://images\.gog-cdn\.com/.+",
)


def _is_gog_thumbnail(url: str) -> bool:
    """Return True if *url* looks like a small GOG CDN thumbnail.

    GOG embeds return tiny box-art images from ``images.gog-cdn.com``.
    Any URL from that host is considered a candidate for upgrade.
    """
    return bool(_GOG_CDN_RE.match(url))


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


async def search_steamgriddb_cover(game_title: str) -> str | None:
    """Search SteamGridDB API for a game cover.

    Requires ``settings.steamgriddb_api_key`` (from .env).
    Returns the first 600x900 grid image URL, or None.

    Early exit if no API key is configured.
    """
    api_key = settings.steamgriddb_api_key
    if not api_key:
        logger.debug("SteamGridDB API key not set, skipping")
        return None

    if not game_title or not game_title.strip():
        return None

    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Step 1: Search for game
            search_url = STEAMGRIDDB_SEARCH_URL.format(
                query=urllib.parse.quote(game_title.strip()),
            )
            resp = await client.get(search_url, headers=headers)
            if resp.status_code == 401:
                logger.warning("SteamGridDB API key invalid")
                return None
            resp.raise_for_status()
            data = resp.json()

            # The success/data structure varies - check both
            games_data = data.get("data", [])
            if not games_data:
                logger.debug("No SteamGridDB results", title=game_title)
                return None

            # Try exact title match first
            title_lower = game_title.strip().lower()
            best_match: dict[str, object] | None = None
            for game in games_data:
                if game.get("name", "").lower() == title_lower:
                    best_match = game
                    break

            if not best_match:
                best_match = games_data[0]  # fallback to first result

            game_id = best_match.get("id")
            if not game_id:
                return None

            # Step 2: Get grids for this game
            grids_url = STEAMGRIDDB_GRIDS_URL.format(game_id=game_id)
            grids_resp = await client.get(grids_url, headers=headers)
            if not grids_resp.is_success:
                return None

            grids_data = grids_resp.json()
            grids = grids_data.get("data", [])
            if not grids:
                return None

            # Filter for 600x900 grids (preferred SteamGridDB format)
            for grid in grids:
                if grid.get("width") == 600 and grid.get("height") == 900:
                    url = grid.get("url", "")
                    if url:
                        logger.info(
                            "Found SteamGridDB cover",
                            title=game_title,
                            game_id=game_id,
                        )
                        return cast(str, url)

            # Fallback to first grid
            first = grids[0]
            url = first.get("url", "")
            if url:
                logger.info(
                    "Found SteamGridDB cover (approx)",
                    title=game_title,
                    game_id=game_id,
                )
                return cast(str, url)

    except httpx.TimeoutException:
        logger.warning("SteamGridDB search timed out", title=game_title)
    except httpx.HTTPStatusError as e:
        logger.warning(
            "SteamGridDB HTTP error",
            title=game_title,
            status=e.response.status_code,
        )
    except httpx.RequestError as e:
        logger.warning(
            "SteamGridDB request failed",
            title=game_title,
            error=str(e),
        )
    except Exception as e:
        logger.error(
            "SteamGridDB search failed",
            title=game_title,
            error=str(e),
        )

    return None


async def search_gog_cover(title: str, current_cover_url: str = "") -> str | None:
    """Try to find a higher-resolution cover for a GOG game.

    Strategy:
    1. If we already have a GOG CDN URL, probe common larger-size variants
       on the same CDN path (e.g. ``_cd600`` suffixes).
    2. Search SteamGridDB for the game title (reliable fallback).
    3. Search the Steam store (cross-platform games that also exist on Steam).

    This function does **not** require a GOG authentication token.
    Returns a better cover URL if found, ``None`` otherwise.
    """
    if not title or not title.strip():
        return None

    # --- Strategy 1: probe GOG CDN size variants ---
    if current_cover_url and _is_gog_thumbnail(current_cover_url):
        larger = await _probe_gog_cdn_larger(current_cover_url)
        if larger:
            return larger

    # --- Strategy 2: SteamGridDB (reliable high-quality covers) ---
    sgdb = await search_steamgriddb_cover(title)
    if sgdb:
        return sgdb

    # --- Strategy 3: Steam store search ---
    steam = await search_steam_cover(title)
    if steam:
        return steam

    return None


async def _probe_gog_cdn_larger(url: str) -> str | None:
    """Probe GOG CDN for larger versions of a thumbnail URL.

    GOG CDN images sometimes have size-suffixed variants.  For example::

        images.gog-cdn.com/igmg/abc123.jpg
        images.gog-cdn.com/igmg/abc123_cd600.jpg

    We try common suffixes and return the first one that responds with
    a successful HEAD request **and** a ``Content-Length`` above a minimum
    threshold (10 KB), which indicates a meaningfully larger image.
    """
    # Suffixes ordered from largest to smallest so we grab the best one early.
    suffixes = ["_cd600", "_cd400", "_cd200"]

    # Split on last '.' to insert the suffix before the extension.
    dot_pos = url.rfind(".")
    if dot_pos == -1:
        return None
    base = url[:dot_pos]
    ext = url[dot_pos:]

    min_bytes = 10_240  # 10 KB — tiny thumbnails are well below this

    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
            for suffix in suffixes:
                candidate = f"{base}{suffix}{ext}"
                try:
                    resp = await client.head(candidate)
                    if resp.is_success:
                        length = int(resp.headers.get("content-length", "0"))
                        if length >= min_bytes:
                            logger.info(
                                "Found larger GOG CDN cover",
                                original=url,
                                upgraded=candidate,
                                size_bytes=length,
                            )
                            return candidate
                except httpx.RequestError:
                    continue  # try next suffix
    except Exception as e:
        logger.debug("GOG CDN probe failed", url=url, error=str(e))

    return None


async def search_epic_cover(store_id: str) -> str | None:
    """Extract cover art from Epic Games via Legendary info command.

    Calls ``legendary info <store_id> --json`` and extracts
    the keyImage with type 'DieselGameBoxTall'.

    This requires the 'legendary' CLI to be installed and on PATH.
    Returns the first matching image URL, or None on failure.
    """
    if not store_id:
        return None

    try:
        proc = await asyncio.create_subprocess_exec(
            "legendary", "info", store_id, "--json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.warning(
                "Legendary info failed",
                store_id=store_id,
                error=stderr.decode().strip(),
            )
            return None

        data = json.loads(stdout.decode())

        # Legendary info returns metadata.keyImages array
        metadata = data.get("metadata", {}) or data.get("_metadata", {})
        key_images = metadata.get("keyImages", [])

        # Try to find the tall box art (600x900-ish)
        preferred_types = [
            "DieselGameBoxTall",
            "DieselGameBox",
            "OfferImageTall",
            "Thumbnail",
        ]
        for img_type in preferred_types:
            for img in key_images:
                if img.get("type") == img_type:
                    url = img.get("url", "")
                    if url:
                        logger.info(
                            "Found Epic cover via legendary info",
                            store_id=store_id,
                            type=img_type,
                        )
                        return cast(str, url)

        # Fallback: return any image URL
        for img in key_images:
            url = img.get("url", "")
            if url:
                logger.info("Found Epic cover (fallback)", store_id=store_id)
                return cast(str, url)

    except FileNotFoundError:
        logger.warning("Legendary CLI not found, cannot get Epic cover")
    except json.JSONDecodeError as e:
        logger.warning(
            "Failed to parse Legendary info JSON",
            store_id=store_id,
            error=str(e),
        )
    except Exception as e:
        logger.error(
            "Epic cover search failed",
            store_id=store_id,
            error=str(e),
        )

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

    is_gog = game.store == StoreSource.GOG
    has_cover = bool(game.cover_art_url)
    has_gog_thumb = is_gog and has_cover and _is_gog_thumbnail(game.cover_art_url)

    # Skip only when the cover is already good.
    # GOG games with small CDN thumbnails are NOT skipped — they need upgrading.
    if has_cover and not has_gog_thumb:
        logger.debug("Game already has cover, skipping", title=game.title)
        return False

    # Multi-source cover art strategy
    cover_url = None

    # Source 1 (GOG only): try GOG CDN upsizing + SteamGridDB/Steam fallback
    if is_gog:
        cover_url = await search_gog_cover(game.title, game.cover_art_url)

    # Source 2: Steam store search (catches cross-platform games)
    if not cover_url:
        cover_url = await search_steam_cover(game.title)

    # Source 3: SteamGridDB (fallback for anything else)
    if not cover_url:
        cover_url = await search_steamgriddb_cover(game.title)

    # Note: search_epic_cover() requires store_id which is not available
    # in the current domain model. Will be added in a future update.

    if cover_url:
        try:
            domain_game = repo.get(gid)
            if domain_game:
                domain_game.set_cover_art(cover_url)
                repo.save(domain_game)
                logger.info(
                    "Cover updated successfully",
                    title=game.title,
                    game_id=game_id,
                )
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
    missing = [
        g for g in all_games
        if not g.cover_art_url
        or (
            g.store == StoreSource.GOG
            and _is_gog_thumbnail(g.cover_art_url)
        )
    ]

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
