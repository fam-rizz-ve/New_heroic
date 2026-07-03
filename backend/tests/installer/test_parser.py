"""Tests for installer YAML parser."""

import pytest

from app.installer.parser import InstallerParseError, parse_installer


class TestParseInstaller:
    """Tests for the YAML installer parser."""

    VALID_YAML = """
name: Test Game
game_slug: test-game
version: "1.0"
year: 2024
runner: wine
description: A test game installer

files:
  setup.exe: https://example.com/setup.exe

installer:
  - extract:
      description: Extracting game files
      file: setup.exe
      dst: $GAMEDIR
  - chmodx:
      description: Making executable
      file: game.exe
  - wine:
      description: Running game
      executable: game.exe
"""

    def test_parse_valid_installer(self) -> None:
        """Parse a full valid YAML installer."""
        manifest = parse_installer(self.VALID_YAML)
        assert manifest.name == "Test Game"
        assert manifest.game_slug == "test-game"
        assert manifest.version == "1.0"
        assert manifest.runner == "wine"
        assert len(manifest.files) == 1
        assert manifest.files[0].name == "setup.exe"
        assert len(manifest.steps) == 3

    def test_parse_minimal_installer(self) -> None:
        """Parse a minimal valid YAML installer."""
        yaml = """
name: Minimal Game
game_slug: minimal
version: "1.0"
runner: native

installer:
  - execute:
      command: echo "hello"
"""
        manifest = parse_installer(yaml)
        assert manifest.name == "Minimal Game"
        assert len(manifest.steps) == 1

    def test_missing_name_raises(self) -> None:
        """Missing 'name' field should raise."""
        with pytest.raises(InstallerParseError, match="'name' field"):
            parse_installer("game_slug: test\nversion: '1.0'\ninstaller: []")

    def test_missing_game_slug_raises(self) -> None:
        """Missing 'game_slug' field should raise."""
        with pytest.raises(InstallerParseError, match="'game_slug' field"):
            parse_installer("name: Test\nversion: '1.0'\ninstaller: []")

    def test_invalid_yaml_raises(self) -> None:
        """Invalid YAML content should raise."""
        with pytest.raises(InstallerParseError, match="Invalid YAML"):
            parse_installer("{invalid: yaml: broken}")

    def test_not_a_mapping_raises(self) -> None:
        """Non-mapping YAML should raise."""
        with pytest.raises(InstallerParseError, match="must be a mapping"):
            parse_installer("[1, 2, 3]")

    def test_empty_installer(self) -> None:
        """Manifest with empty installer list should parse."""
        manifest = parse_installer(
            "name: Empty\nversion: '1.0'\ngame_slug: empty\ninstaller: []"
        )
        assert manifest.name == "Empty"
        assert len(manifest.steps) == 0
