"""API endpoints for game and library management."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import TypeAdapter

from app.api.dependencies import get_use_cases
from app.core.domain.enums import RunnerType, StoreSource
from app.core.domain.library import DuplicateGameError
from app.core.domain.value_objects import GameId, LibraryId
from app.core.use_cases.library import AddGameRequest, LibraryUseCases
from app.schemas.game import (
    GameActionResponse,
    GameCreate,
    GameResponse,
    LibraryCreate,
    LibraryResponse,
)

router = APIRouter(tags=["games"])

@router.get("/libraries", response_model=list[LibraryResponse])
async def list_libraries(
    use_cases: LibraryUseCases = Depends(get_use_cases),
) -> list[LibraryResponse]:
    """List all libraries."""
    libraries = use_cases._library_repo.list_all()
    return [
        _library_to_response(lib)
        for lib in libraries
    ]


@router.post(
    "/libraries",
    response_model=LibraryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_library(
    request: LibraryCreate,
    use_cases: LibraryUseCases = Depends(get_use_cases),
) -> LibraryResponse:
    """Create a new library."""
    try:
        store_source = StoreSource(request.store_source)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid store source: '{request.store_source}'. "
            f"Valid options: {[s.value for s in StoreSource]}",
        )

    from app.core.domain.library import Library
    from app.core.domain.value_objects import LibraryId

    library = Library(
        id=LibraryId.generate(),
        name=request.name,
        store_source=store_source,
    )
    use_cases._library_repo.save(library)

    return _library_to_response(library)


@router.get("/libraries/{library_id}/games", response_model=list[GameResponse])
async def list_games(
    library_id: str,
    use_cases: LibraryUseCases = Depends(get_use_cases),
) -> list[GameResponse]:
    """List all games in a library."""
    try:
        lid = LibraryId(UUID(library_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid library ID format",
        )

    try:
        results = use_cases.list_library_games(lid)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return [_game_result_to_response(r) for r in results]


@router.post(
    "/libraries/{library_id}/games",
    response_model=GameResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_game(
    library_id: str,
    request: GameCreate,
    use_cases: LibraryUseCases = Depends(get_use_cases),
) -> GameResponse:
    """Add a new game to a library."""
    try:
        lid = LibraryId(UUID(library_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid library ID format",
        )

    try:
        store = StoreSource(request.store)
        runner = RunnerType(request.runner)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid store or runner. Store: {[s.value for s in StoreSource]}, "
            f"Runner: {[r.value for r in RunnerType]}",
        )

    add_request = AddGameRequest(
        title=request.title,
        store=store,
        runner=runner,
        description=request.description,
        cover_art_url=request.cover_art_url,
    )

    try:
        result = use_cases.add_game_to_library(lid, add_request)
    except DuplicateGameError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    # Fetch full game from repo for accurate timestamps
    game = use_cases._game_repo.get(GameId(UUID(result.id)))
    if game:
        return _game_to_response(result, game)
    return _game_result_to_response(result)


@router.get("/games/{game_id}", response_model=GameResponse)
async def get_game(
    game_id: str,
    use_cases: LibraryUseCases = Depends(get_use_cases),
) -> GameResponse:
    """Get details of a specific game."""
    try:
        gid = GameId(UUID(game_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid game ID format",
        )

    result = use_cases.get_game(gid)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game with id '{game_id}' not found",
        )

    # Fetch full game from repo for accurate timestamps
    game = use_cases._game_repo.get(gid)
    if game:
        return _game_to_response(result, game)
    return _game_result_to_response(result)


@router.post("/games/{game_id}/install", response_model=GameActionResponse)
async def install_game(
    game_id: str,
    use_cases: LibraryUseCases = Depends(get_use_cases),
) -> GameActionResponse:
    """Start installation for a game."""
    try:
        gid = GameId(UUID(game_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid game ID format",
        )

    try:
        result = use_cases.install_game(gid)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    return GameActionResponse(
        message="Installation started",
        game=_game_result_to_response(result),
    )


@router.post("/games/{game_id}/uninstall", response_model=GameActionResponse)
async def uninstall_game(
    game_id: str,
    use_cases: LibraryUseCases = Depends(get_use_cases),
) -> GameActionResponse:
    """Uninstall a game."""
    try:
        gid = GameId(UUID(game_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid game ID format",
        )

    try:
        result = use_cases.uninstall_game(gid)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    return GameActionResponse(
        message="Game uninstalled",
        game=_game_result_to_response(result),
    )


@router.post("/games/{game_id}/launch", response_model=GameActionResponse)
async def launch_game(
    game_id: str,
    use_cases: LibraryUseCases = Depends(get_use_cases),
) -> GameActionResponse:
    """Launch a game."""
    try:
        gid = GameId(UUID(game_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid game ID format",
        )

    try:
        result = use_cases.launch_game(gid)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    return GameActionResponse(
        message="Game launched",
        game=_game_result_to_response(result),
    )


@router.post("/games/{game_id}/close", response_model=GameActionResponse)
async def close_game(
    game_id: str,
    use_cases: LibraryUseCases = Depends(get_use_cases),
) -> GameActionResponse:
    """Close a running game."""
    try:
        gid = GameId(UUID(game_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid game ID format",
        )

    try:
        result = use_cases.close_game(gid)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    return GameActionResponse(
        message="Game closed",
        game=_game_result_to_response(result),
    )


def _game_result_to_response(result: object) -> GameResponse:
    """Convert a GameResult or similar result to a GameResponse.

    Prefers the repository-backed _game_to_response when the domain
    Game object is available. This function serves as a fallback when
    only a result DTO is available.
    """
    # Use TypeAdapter for safe type coercion of datetime fields
    ta = TypeAdapter(datetime)
    return GameResponse(
        id=getattr(result, "id", ""),
        title=getattr(result, "title", ""),
        store=getattr(result, "store", ""),
        runner=getattr(result, "runner", ""),
        status=getattr(result, "status", ""),
        description=getattr(result, "description", ""),
        cover_art_url=getattr(result, "cover_art_url", ""),
        install_path=getattr(result, "install_path", None),
        executable_path=getattr(result, "executable_path", None),
        last_played=(
            ta.validate_python(getattr(result, "last_played", None))
            if getattr(result, "last_played", None)
            else None
        ),
        total_play_time_seconds=getattr(result, "total_play_time_seconds", 0),
        created_at=ta.validate_python(getattr(result, "created_at", "1970-01-01T00:00:00")),
        updated_at=ta.validate_python(getattr(result, "updated_at", "1970-01-01T00:00:00")),
    )


def _game_to_response(result: object, game: object) -> GameResponse:
    """Convert a GameResult and a domain Game to a GameResponse.

    Uses the Game object for timestamp fields and the result for
    all other fields. This ensures accurate timestamps when the
    domain Game is available from the repository.
    """
    from datetime import datetime as dt

    return GameResponse(
        id=getattr(result, "id", ""),
        title=getattr(result, "title", ""),
        store=getattr(result, "store", ""),
        runner=getattr(result, "runner", ""),
        status=getattr(result, "status", ""),
        description=getattr(result, "description", ""),
        cover_art_url=getattr(result, "cover_art_url", ""),
        install_path=getattr(result, "install_path", None),
        executable_path=getattr(result, "executable_path", None),
        last_played=getattr(game, "last_played", None),
        total_play_time_seconds=getattr(result, "total_play_time_seconds", 0),
        created_at=getattr(game, "created_at", dt.now()),
        updated_at=getattr(game, "updated_at", dt.now()),
    )


def _library_to_response(library: object) -> LibraryResponse:
    """Convert a domain Library to a LibraryResponse."""
    from app.core.domain.library import Library as DomainLibrary

    if not isinstance(library, DomainLibrary):
        return LibraryResponse(
            id=str(getattr(library, "id", "")),
            name=getattr(library, "name", ""),
            store_source=str(getattr(library, "store_source", "")),
            game_count=getattr(library, "game_count", 0),
            created_at=getattr(library, "created_at", datetime.now()),
            updated_at=getattr(library, "updated_at", datetime.now()),
        )
    return LibraryResponse(
        id=str(library.id.value),
        name=library.name,
        store_source=library.store_source.value,
        game_count=library.game_count,
        created_at=library.created_at,
        updated_at=library.updated_at,
    )
