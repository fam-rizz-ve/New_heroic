"""API endpoints for store integrations."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.store import (
    AuthRequest,
    AuthResponse,
    AuthUrlResponse,
    StoreGameSchema,
    StoreInfo,
    StoreStatusResponse,
)
from app.stores.manager import StoreManager

router = APIRouter(prefix="/stores", tags=["stores"])

# Module-level singleton for development.
# Replaced with DI container wiring in production.
_manager: StoreManager | None = None


def get_store_manager() -> StoreManager:
    """Dependency: get the store manager singleton."""
    global _manager
    if _manager is None:
        _manager = StoreManager.create_default()
    return _manager


@router.get("", response_model=list[StoreInfo])
async def list_stores(
    manager: StoreManager = Depends(get_store_manager),
) -> list[StoreInfo]:
    """List all available store integrations."""
    stores_data = manager.list_available()
    return [StoreInfo(**s) for s in stores_data]


@router.post("/{store_name}/auth", response_model=AuthResponse)
async def authenticate_store(
    store_name: str,
    request: AuthRequest,
    manager: StoreManager = Depends(get_store_manager),
) -> AuthResponse:
    """Authenticate with a store using an auth code.

    Args:
        store_name: The store name (e.g., "epic", "gog").
        request: The auth code or token.

    Returns:
        AuthResponse with success status and optional username.

    Raises:
        HTTPException 404: If the store is not found.
        HTTPException 401: If authentication fails.
    """
    store = manager.get(store_name)
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store '{store_name}' not found",
        )

    try:
        credentials = await store.authenticate(request.code)
        return AuthResponse(
            success=True,
            username=credentials.username,
            message=f"Authenticated with {store.display_name}",
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/{store_name}/auth/browser", response_model=AuthResponse)
async def browser_auth(
    store_name: str,
    manager: StoreManager = Depends(get_store_manager),
) -> AuthResponse:
    """Authenticate with a store via automatic browser-based OAuth.

    Starts a local callback server, opens the browser to the OAuth URL,
    waits for the redirect, and authenticates using the captured code.

    This endpoint may take up to 120 seconds to respond while waiting
    for the user to complete the OAuth flow in their browser.

    Args:
        store_name: The store name (e.g., "epic", "gog").

    Returns:
        AuthResponse with success status and optional username.

    Raises:
        HTTPException 404: If the store is not found.
        HTTPException 401: If authentication fails.
        HTTPException 408: If the authentication times out.
    """
    store = manager.get(store_name)
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store '{store_name}' not found",
        )

    try:
        credentials = await store.start_browser_auth()
        return AuthResponse(
            success=True,
            username=credentials.username,
            message=f"Authenticated with {store.display_name}",
        )
    except TimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=str(e),
        )
    except NotImplementedError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.get("/{store_name}/auth-url", response_model=AuthUrlResponse)
async def get_store_auth_url(
    store_name: str,
    manager: StoreManager = Depends(get_store_manager),
) -> AuthUrlResponse:
    """Get the OAuth login URL for a store.

    Args:
        store_name: The store name (e.g., "epic", "gog").

    Returns:
        AuthUrlResponse with the login URL and instructions.

    Raises:
        HTTPException 404: If the store is not found.
    """
    store = manager.get(store_name)
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store '{store_name}' not found",
        )

    auth_url = await store.get_auth_url()
    instructions = await store.get_auth_instructions()
    return AuthUrlResponse(
        auth_url=auth_url,
        instructions=instructions,
        store_name=store_name,
    )


@router.get("/{store_name}/status", response_model=StoreStatusResponse)
async def get_store_status(
    store_name: str,
    manager: StoreManager = Depends(get_store_manager),
) -> StoreStatusResponse:
    """Get the authentication and installation status of a store.

    Args:
        store_name: The store name (e.g., "epic", "gog").

    Returns:
        StoreStatusResponse with name, display_name, is_authenticated, is_installed.

    Raises:
        HTTPException 404: If the store is not found.
    """
    store = manager.get(store_name)
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store '{store_name}' not found",
        )

    is_authenticated = await store.is_authenticated()
    is_installed = await store.check_installed()
    return StoreStatusResponse(
        name=store.name,
        display_name=store.display_name,
        is_authenticated=is_authenticated,
        is_installed=is_installed,
    )


@router.get("/{store_name}/games", response_model=list[StoreGameSchema])
async def list_store_games(
    store_name: str,
    manager: StoreManager = Depends(get_store_manager),
) -> list[StoreGameSchema]:
    """List all games available from a store.

    Args:
        store_name: The store name (e.g., "epic", "gog").

    Returns:
        A list of StoreGameSchema with game metadata.

    Raises:
        HTTPException 404: If the store is not found.
        HTTPException 502: If the store CLI fails.
    """
    store = manager.get(store_name)
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store '{store_name}' not found",
        )

    try:
        games = await store.list_games()
        return [
            StoreGameSchema(
                store_id=g.store_id,
                title=g.title,
                description=g.description,
                cover_art_url=g.cover_art_url,
                developer=g.developer,
                publisher=g.publisher,
                release_date=g.release_date,
                genres=g.genres,
            )
            for g in games
        ]
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
