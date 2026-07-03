"""FastAPI application factory for New Heroic backend."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.diagnostics import router as diagnostics_router
from app.api.game_settings import router as game_settings_router
from app.api.games import router as games_router
from app.api.games_v2 import router as library_v2_router
from app.api.health import router as health_router
from app.api.installer import router as installer_router
from app.api.runners import router as runners_router
from app.api.stores import router as stores_router
from app.api.wine_manager import router as wine_manager_router
from app.core.config import settings
from app.core.container import ApplicationContainer
from app.core.domain.enums import StoreSource
from app.core.domain.library import Library
from app.core.domain.value_objects import LibraryId
from app.core.logging import configure_logging

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: auto-create default library on startup.

    The default library serves as the unified game collection
    (Heroic-style), removing the need for manual library creation.
    """
    # Initialize use cases singleton to ensure the same repository
    # is used by both lifespan and API endpoints.
    from app.api.dependencies import get_use_cases

    use_cases = get_use_cases()
    repo = use_cases._library_repo
    libraries = repo.list_all()
    if not libraries:
        default_lib = Library(
            id=LibraryId.generate(),
            name="Game Library",
            store_source=StoreSource.LOCAL,
        )
        repo.save(default_lib)
        logger.info("Default library created", name=default_lib.name)
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    # Configure logging early
    configure_logging(debug=settings.debug)

    # Create FastAPI app with lifespan
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Set up dependency injection container
    container = ApplicationContainer()
    app.container = container  # type: ignore[attr-defined]

    # Register routers
    app.include_router(health_router, prefix="/api", tags=["health"])
    app.include_router(games_router, prefix="/api", tags=["games"])
    app.include_router(library_v2_router, prefix="/api")
    app.include_router(installer_router, prefix="/api", tags=["installer"])
    app.include_router(runners_router, prefix="/api", tags=["runners"])
    app.include_router(stores_router, prefix="/api", tags=["stores"])
    app.include_router(wine_manager_router, prefix="/api", tags=["wine"])
    app.include_router(diagnostics_router, prefix="/api", tags=["diagnostics"])
    app.include_router(game_settings_router, prefix="/api", tags=["game_settings"])

    # Log startup
    logger.info(
        "application_started",
        app_name=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level,
    )
