"""Tests for per-game settings storage."""

from __future__ import annotations

import json
import tempfile
from collections.abc import Generator

import pytest

from app.core.game_settings import GameSettings, GameSettingsStore


class TestGameSettingsDefaults:
    """Tests for GameSettings default values."""

    def test_default_runner(self) -> None:
        """Default runner should be 'wine'."""
        settings = GameSettings(game_id="test-game")
        assert settings.runner == "wine"

    def test_default_dxvk_enabled(self) -> None:
        """DXVK should be enabled by default."""
        settings = GameSettings(game_id="test-game")
        assert settings.dxvk is True

    def test_default_vkd3d_enabled(self) -> None:
        """VKD3D should be enabled by default."""
        settings = GameSettings(game_id="test-game")
        assert settings.vkd3d is True

    def test_default_fsr_disabled(self) -> None:
        """FSR should be disabled by default."""
        settings = GameSettings(game_id="test-game")
        assert settings.fsr is False

    def test_default_game_mode_enabled(self) -> None:
        """GameMode should be enabled by default."""
        settings = GameSettings(game_id="test-game")
        assert settings.game_mode is True

    def test_default_mangohud_disabled(self) -> None:
        """MangoHud should be disabled by default."""
        settings = GameSettings(game_id="test-game")
        assert settings.mangohud is False


class TestGameSettingsStore:
    """Tests for GameSettingsStore persistence."""

    @pytest.fixture
    def store(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> Generator[GameSettingsStore, None, None]:
        """Create a GameSettingsStore with a temp directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            monkeypatch.setattr(
                "app.core.game_settings.SETTINGS_DIR",
                tmp_dir,
            )
            yield GameSettingsStore()

    def test_get_settings_defaults(self, store: GameSettingsStore) -> None:
        """Getting settings for a game with no saved file returns defaults."""
        settings = store.get_settings("nonexistent-game")
        assert isinstance(settings, GameSettings)
        assert settings.game_id == "nonexistent-game"
        assert settings.runner == "wine"

    def test_save_and_load(self, store: GameSettingsStore) -> None:
        """Saving then loading settings should return the same values."""
        original = GameSettings(
            game_id="test-game",
            runner="proton",
            wine_version="GE-Proton8-25",
            wine_prefix="/custom/wineprefix",
            arguments="--opengl",
            env_vars={"DRI_PRIME": "1"},
            dxvk=True,
            vkd3d=False,
            fsr=True,
            fsr_quality="performance",
            game_mode=False,
            mangohud=True,
        )
        store.save_settings(original)

        loaded = store.get_settings("test-game")
        assert loaded.game_id == "test-game"
        assert loaded.runner == "proton"
        assert loaded.wine_version == "GE-Proton8-25"
        assert loaded.wine_prefix == "/custom/wineprefix"
        assert loaded.arguments == "--opengl"
        assert loaded.env_vars == {"DRI_PRIME": "1"}
        assert loaded.dxvk is True
        assert loaded.vkd3d is False
        assert loaded.fsr is True
        assert loaded.fsr_quality == "performance"
        assert loaded.game_mode is False
        assert loaded.mangohud is True

    def test_save_updates_existing(self, store: GameSettingsStore) -> None:
        """Saving new values for an existing game should overwrite."""
        store.save_settings(GameSettings(game_id="test-game", runner="wine"))
        store.save_settings(GameSettings(game_id="test-game", runner="proton"))

        loaded = store.get_settings("test-game")
        assert loaded.runner == "proton"

    def test_delete_settings(self, store: GameSettingsStore) -> None:
        """Deleting settings should remove the file and return defaults."""
        store.save_settings(GameSettings(game_id="test-game", runner="proton"))
        store.delete_settings("test-game")

        # After deletion, should get defaults
        loaded = store.get_settings("test-game")
        assert loaded.runner == "wine"

    def test_delete_nonexistent_raises(self, store: GameSettingsStore) -> None:
        """Deleting settings for a game with no saved file should raise."""
        with pytest.raises(FileNotFoundError, match="No settings found"):
            store.delete_settings("nonexistent-game")

    def test_invalid_json_returns_defaults(
        self,
        store: GameSettingsStore,
    ) -> None:
        """Corrupted JSON file should return default settings."""
        # Write invalid JSON directly
        settings_path = store._settings_path("corrupted-game")
        with open(settings_path, "w") as f:
            f.write("invalid json content")

        settings = store.get_settings("corrupted-game")
        assert settings.runner == "wine"
        assert settings.game_id == "corrupted-game"

    def test_file_contents_structure(
        self,
        store: GameSettingsStore,
    ) -> None:
        """Saved JSON file should have the expected structure."""
        settings = GameSettings(
            game_id="test-game",
            runner="wine",
            wine_version=None,
            arguments="-test",
        )
        store.save_settings(settings)

        settings_path = store._settings_path("test-game")
        with open(settings_path) as f:
            data = json.load(f)

        assert data["game_id"] == "test-game"
        assert data["runner"] == "wine"
        assert data["wine_version"] is None
        assert data["arguments"] == "-test"
        assert "env_vars" in data
        assert "dxvk" in data
        assert "vkd3d" in data
        assert "fsr" in data
        assert "game_mode" in data
