"""Unified API endpoints for the game library (Heroic-style).

Provides a single-library experience where all games live in one place
regardless of store source. Filters are handled via query parameters.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_use_cases
from app.core.domain.enums import RunnerType, StoreSource
from app.core.domain.library import DuplicateGameError
from app.core.domain.value_objects import GameId, GameTitle
from app.core.use_cases.library import AddGameRequest, GameResult, LibraryUseCases
from app.schemas.game import (
    GameActionResponse,
    GameCreate,
    GameResponse,
)
from app.stores.manager import StoreManager

router = APIRouter(tags=["library"])


def _parse_game_id(game_id: str) -> GameId:
    """Parse a UUID string into a GameId, or raise 400."""
    try:
        return GameId(UUID(game_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid game ID format",
        )


def _game_result_to_response(result: GameResult) -> GameResponse:
    """Convert a GameResult to a Pydantic GameResponse."""
    return GameResponse(
        id=result.id,
        title=result.title,
        store=result.store,
        runner=result.runner,
        status=result.status,
        description=result.description,
        cover_art_url=result.cover_art_url,
        store_id=result.store_id,
        install_path=result.install_path,
        executable_path=result.executable_path,
        last_played=(datetime.fromisoformat(result.last_played) if result.last_played else None),
        total_play_time_seconds=result.total_play_time_seconds,
        is_favorite=result.is_favorite,
        created_at=datetime.fromisoformat(result.created_at),
        updated_at=datetime.fromisoformat(result.updated_at),
    )


@router.get("/library/games", response_model=list[GameResponse])
async def list_games(
    store: str | None = Query(None, description="Filter by store source"),
    status: str | None = Query(None, description="Filter by game status"),
    search: str | None = Query(None, description="Search by title"),
    favorite: bool | None = Query(None, description="Filter by favorite status"),
    use_cases: LibraryUseCases = Depends(get_use_cases),
) -> list[GameResponse]:
    """List all games with optional filters (heroic-style unified library)."""
    results = use_cases.list_all_games(store=store, status=status, search=search, favorite=favorite)
    return [_game_result_to_response(r) for r in results]


@router.post(
    "/library/games",
    response_model=GameResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_game(
    request: GameCreate,
    use_cases: LibraryUseCases = Depends(get_use_cases),
) -> GameResponse:
    """Add a new game to the unified library."""
    try:
        store = StoreSource(request.store)
        runner = RunnerType(request.runner)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid store or runner",
        )

    # Find or create the default library
    libraries = use_cases._library_repo.list_all()
    if not libraries:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default library not initialized",
        )
    library_id = libraries[0].id

    add_request = AddGameRequest(
        title=request.title,
        store=store,
        runner=runner,
        description=request.description or "",
        cover_art_url=request.cover_art_url or "",
    )

    try:
        result = use_cases.add_game_to_library(library_id, add_request)
    except (DuplicateGameError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    return _game_result_to_response(result)


@router.get("/library/games/{game_id}", response_model=GameResponse)
async def get_game(
    game_id: str,
    use_cases: LibraryUseCases = Depends(get_use_cases),
) -> GameResponse:
    """Get details of a specific game."""
    gid = _parse_game_id(game_id)
    result = use_cases.get_game(gid)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game '{game_id}' not found",
        )
    return _game_result_to_response(result)


@router.post("/library/games/{game_id}/favorite", response_model=GameResponse)
async def toggle_favorite(
    game_id: str,
    use_cases: LibraryUseCases = Depends(get_use_cases),
) -> GameResponse:
    """Toggle the favorite status of a game."""
    gid = _parse_game_id(game_id)
    try:
        result = use_cases.toggle_favorite(gid)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return _game_result_to_response(result)


@router.post("/library/games/{game_id}/install", response_model=GameActionResponse)
async def install_game(
    game_id: str,
    use_cases: LibraryUseCases = Depends(get_use_cases),
) -> GameActionResponse:
    """Start game installation."""
    gid = _parse_game_id(game_id)
    try:
        result = use_cases.install_game(gid)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return GameActionResponse(
        message="Installation started",
        game=_game_result_to_response(result),
    )


@router.post("/library/games/{game_id}/uninstall", response_model=GameActionResponse)
async def uninstall_game(
    game_id: str,
    use_cases: LibraryUseCases = Depends(get_use_cases),
) -> GameActionResponse:
    """Uninstall a game."""
    gid = _parse_game_id(game_id)
    try:
        result = use_cases.uninstall_game(gid)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return GameActionResponse(
        message="Game uninstalled",
        game=_game_result_to_response(result),
    )


@router.post("/library/games/{game_id}/launch", response_model=GameActionResponse)
async def launch_game(
    game_id: str,
    use_cases: LibraryUseCases = Depends(get_use_cases),
) -> GameActionResponse:
    """Launch a game."""
    gid = _parse_game_id(game_id)
    try:
        result = use_cases.launch_game(gid)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return GameActionResponse(
        message="Game launched",
        game=_game_result_to_response(result),
    )


@router.post("/library/games/{game_id}/close", response_model=GameActionResponse)
async def close_game(
    game_id: str,
    use_cases: LibraryUseCases = Depends(get_use_cases),
) -> GameActionResponse:
    """Close a running game."""
    gid = _parse_game_id(game_id)
    try:
        result = use_cases.close_game(gid)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return GameActionResponse(
        message="Game closed",
        game=_game_result_to_response(result),
    )


@router.post("/stores/{store_name}/sync")
async def sync_store_games(
    store_name: str,
    use_cases: LibraryUseCases = Depends(get_use_cases),
    manager: StoreManager = Depends(lambda: StoreManager.create_default()),
) -> dict[str, object]:
    """Import games from a store into the unified library."""
    store = manager.get(store_name)
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store '{store_name}' not found",
        )

    try:
        store_games = await store.list_games()
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    # Get the default library
    libraries = use_cases._library_repo.list_all()
    if not libraries:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default library not initialized",
        )
    library = libraries[0]

    # Build set of existing (store, title_lower) to avoid duplicates
    existing_titles: set[str] = set()
    for g in library.games.values():
        if g.store.value == store_name:
            existing_titles.add(g.title.value.lower())

    imported = 0
    errors: list[str] = []

    from app.core.domain.game import Game as DomainGame

    for sg in store_games:
        try:
            title_lower = sg.title.lower()
            if title_lower in existing_titles:
                continue  # skip duplicate
            existing_titles.add(title_lower)

            title = GameTitle(sg.title)
            domain_game = DomainGame(
                id=GameId.generate(),
                title=title,
                store=StoreSource(store_name),
                runner=RunnerType.WINE,
                description=sg.description,
                cover_art_url=sg.cover_art_url,
                store_id=sg.store_id,
            )
            library.add_game(domain_game)
            use_cases._game_repo.save(domain_game)
            imported += 1
        except DuplicateGameError:
            continue
        except Exception as e:
            errors.append(f"{sg.title}: {e}")

    use_cases._library_repo.save(library)

    return {
        "imported": imported,
        "errors": errors,
        "total": len(store_games),
        "store": store_name,
    }
