"""Tests for DiagnosticsManager."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.diagnostics.manager import DiagnosticsManager
from app.diagnostics.models import DiagnosticPattern


class TestDiagnosticsManager:
    """Tests for DiagnosticsManager."""

    def test_create_default(self) -> None:
        """Create manager with default patterns."""
        manager = DiagnosticsManager.create_default()
        assert len(manager.list_patterns()) > 0

    def test_register_custom_pattern(self) -> None:
        """Register a custom diagnostic pattern."""
        manager = DiagnosticsManager()
        pattern = DiagnosticPattern(
            name="custom_test",
            description="Test pattern",
            regex=r"custom.*error",
            issue_type="custom",
            severity="error",
            title="Custom Error",
            suggestion="Custom fix",
        )
        manager.register_pattern(pattern)
        assert pattern in manager.list_patterns()

    def test_register_duplicate_pattern_overwrites(self) -> None:
        """Registering duplicate pattern name should overwrite."""
        manager = DiagnosticsManager()
        p1 = DiagnosticPattern(
            name="test",
            description="Original",
            regex=r"original",
            issue_type="test",
            severity="error",
            title="Original",
            suggestion="Fix 1",
        )
        p2 = DiagnosticPattern(
            name="test",
            description="Overwritten",
            regex=r"overwritten",
            issue_type="test",
            severity="warning",
            title="Overwritten",
            suggestion="Fix 2",
        )
        manager.register_pattern(p1)
        manager.register_pattern(p2)
        patterns = manager.list_patterns()
        assert len(patterns) == 1
        assert patterns[0].description == "Overwritten"

    def test_analyze_text(self) -> None:
        """Analyze raw log text."""
        manager = DiagnosticsManager.create_default()
        log_text = 'err:module:import_dll: Library xinput1_3.dll not found\n'
        result = manager.analyze_text(log_text, runner="wine")
        assert len(result.issues) > 0
        assert result.runner == "wine"
        assert result.log_line_count == 1

    def test_analyze_text_clean(self) -> None:
        """Analyze clean log text should return no issues."""
        manager = DiagnosticsManager.create_default()
        log_text = "normal log message\nanother normal line\n"
        result = manager.analyze_text(log_text, runner="native")
        assert len(result.issues) == 0

    def test_analyze_text_empty(self) -> None:
        """Analyze empty text should return result with no issues."""
        manager = DiagnosticsManager.create_default()
        result = manager.analyze_text("", runner="wine")
        assert len(result.issues) == 0
        assert result.log_line_count == 0

    def test_analyze_file(self, tmp_path: Path) -> None:
        """Analyze a log file."""
        log_file = tmp_path / "game.log"
        log_file.write_text('err:module:import_dll: Library d3dx9_43.dll not found\n')
        manager = DiagnosticsManager.create_default()
        result = manager.analyze_file(str(log_file), runner="wine")
        assert len(result.issues) > 0
        assert result.log_path == str(log_file)

    def test_analyze_file_not_found(self) -> None:
        """Analyze nonexistent file should raise FileNotFoundError."""
        manager = DiagnosticsManager.create_default()
        with pytest.raises(FileNotFoundError):
            manager.analyze_file("/nonexistent/path.log", runner="wine")

    def test_summary_generation(self) -> None:
        """Result summary should be generated from issues."""
        manager = DiagnosticsManager.create_default()
        log_text = 'err:module:import_dll: Library test.dll not found\n'
        result = manager.analyze_text(log_text, runner="wine")
        assert isinstance(result.summary, str)
        assert len(result.summary) > 0

    def test_list_patterns_returns_copy(self) -> None:
        """list_patterns should return a copy, not internal list."""
        manager = DiagnosticsManager.create_default()
        patterns = manager.list_patterns()
        original_count = len(patterns)
        # Modifying the returned list should not affect the manager
        patterns.clear()
        assert len(manager.list_patterns()) == original_count
