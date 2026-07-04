"""Store manager for discovering and accessing store integrations."""

from __future__ import annotations

import structlog

from app.stores.base import StoreBase
from app.stores.epic import EpicStore
from app.stores.gog import GOGStore
from app.stores.steam import SteamStore


class StoreManager:
    """Registry and factory for store integrations.

    Stores are registered by name. Provides discovery and access methods.
    """

    def __init__(self) -> None:
        self._stores: dict[str, StoreBase] = {}
        self.logger = structlog.get_logger("app.stores.StoreManager")

    def register(self, store: StoreBase) -> None:
        """Register a store integration.

        Args:
            store: A store integration instance.
        """
        self._stores[store.name] = store
        self.logger.debug("Store registered", store=store.name)

    def get(self, name: str) -> StoreBase | None:
        """Get a store by name.

        Args:
            name: The store name (e.g., "epic", "gog").

        Returns:
            The store integration or None if not registered.
        """
        store = self._stores.get(name)
        if store:
            self.logger.debug("Store accessed", store=name)
        return store

    def list_available(self) -> list[dict[str, str]]:
        """List all registered stores with their display names.

        Returns:
            A list of dicts with "name" and "display_name" keys.
        """
        return [
            {
                "name": name,
                "display_name": store.display_name,
            }
            for name, store in self._stores.items()
        ]

    @classmethod
    def create_default(cls) -> StoreManager:
        """Create a StoreManager with all known stores registered.

        Returns:
            A StoreManager instance with Epic and GOG registered.
        """
        manager = cls()
        manager.register(EpicStore())
        manager.register(GOGStore())
        manager.register(SteamStore())
        manager.logger.info("Default stores registered", count=len(manager._stores))
        return manager
