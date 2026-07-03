"""Tests for RunnerManager."""

from __future__ import annotations

from app.runners.manager import RunnerManager
from app.runners.native import NativeRunner


class TestRunnerManager:
    """Tests for the RunnerManager class."""

    def test_register_and_get(self) -> None:
        """Test registering and retrieving a runner."""
        manager = RunnerManager()
        native = NativeRunner()
        manager.register(native)
        assert manager.get("native") is native
        assert manager.get("nonexistent") is None

    def test_list_available(self) -> None:
        """Test listing available runners."""
        manager = RunnerManager()
        manager.register(NativeRunner())
        stores = manager.list_available()
        assert len(stores) == 1
        assert stores[0]["name"] == "native"

    def test_create_default(self) -> None:
        """Test creating default manager with all runners."""
        manager = RunnerManager.create_default()
        assert manager.get("native") is not None
        assert manager.get("wine") is not None
        assert manager.get("proton") is not None
