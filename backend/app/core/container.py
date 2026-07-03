"""Dependency injection container using dependency-injector.

Defines the application's dependency graph for testability
and clean architecture separation.
"""

from dependency_injector import containers, providers

from app.core.config import settings
from app.core.repositories.in_memory import (
    InMemoryGameRepository,
    InMemoryLibraryRepository,
)
from app.core.use_cases.library import LibraryUseCases
from app.installer.manager import InstallerManager
from app.runners.manager import RunnerManager
from app.runners.wine_manager import WineManager
from app.stores.manager import StoreManager


class ApplicationContainer(containers.DeclarativeContainer):
    """Application dependency injection container."""

    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.api.health",
        ]
    )

    # Singleton configuration
    config = providers.Object(settings)

    # Repositories
    game_repository = providers.Singleton(InMemoryGameRepository)
    library_repository = providers.Singleton(InMemoryLibraryRepository)

    # Use cases
    library_use_cases = providers.Factory(
        LibraryUseCases,
        game_repo=game_repository,
        library_repo=library_repository,
    )

    # Runner management
    runner_manager = providers.Singleton(RunnerManager.create_default)

    # Wine/Proton version manager
    wine_manager = providers.Singleton(WineManager)

    # Store integrations
    store_manager = providers.Singleton(StoreManager.create_default)

    # Installer engine
    installer_manager = providers.Singleton(InstallerManager)
