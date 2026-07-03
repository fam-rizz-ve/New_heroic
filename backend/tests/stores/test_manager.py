"""Tests for StoreManager."""

from __future__ import annotations

from app.stores.epic import EpicStore
from app.stores.manager import StoreManager


class TestStoreManager:
    """Tests for StoreManager registration and discovery."""

    def test_register_and_get(self) -> None:
        """Registering a store should make it retrievable by name."""
        manager = StoreManager()
        epic = EpicStore()
        manager.register(epic)

        retrieved = manager.get("epic")
        assert retrieved is epic

        missing = manager.get("nonexistent")
        assert missing is None

    def test_list_available(self) -> None:
        """List available stores should return registered stores."""
        manager = StoreManager()
        manager.register(EpicStore())

        stores = manager.list_available()
        assert len(stores) == 1
        assert stores[0]["name"] == "epic"
        assert stores[0]["display_name"] == "Epic Games"

    def test_create_default(self) -> None:
        """Default manager should have epic and gog registered."""
        manager = StoreManager.create_default()
        assert manager.get("epic") is not None
        assert manager.get("gog") is not None
        assert len(manager.list_available()) == 2
