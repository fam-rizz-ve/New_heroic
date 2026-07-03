"""Tests for the diagnostic detection engine."""

from __future__ import annotations

from app.diagnostics.engine import DiagnosticEngine
from app.diagnostics.models import DiagnosticPattern
from app.diagnostics.parser import LogParser


class TestDiagnosticEngine:
    """Tests for DiagnosticEngine."""

    def test_run_analysis_with_match(self) -> None:
        """Engine should detect issues matching patterns."""
        patterns = [
            DiagnosticPattern(
                name="missing_dll",
                description="Detects missing DLL errors",
                regex=r"err:module:import_dll.*Library\s+(\S+)\.dll",
                issue_type="missing_dll",
                severity="error",
                title="Missing DLL Detected",
                suggestion="Install via winetricks",
            ),
        ]
        engine = DiagnosticEngine(patterns)
        log_text = 'err:module:import_dll: Library xinput1_3.dll not found\n'
        parser = LogParser()
        sections = parser.parse_text(log_text)
        issues = engine.analyze(sections)
        assert len(issues) == 1
        assert issues[0].issue_type == "missing_dll"
        assert issues[0].confidence > 0.5
        assert issues[0].pattern_name == "missing_dll"

    def test_run_analysis_no_match(self) -> None:
        """Engine should return empty list for clean logs."""
        patterns = [
            DiagnosticPattern(
                name="missing_dll",
                description="Test",
                regex=r"err:module:import_dll.*Library\s+\S+\.dll",
                issue_type="missing_dll",
                severity="error",
                title="Test",
                suggestion="Test",
            ),
        ]
        engine = DiagnosticEngine(patterns)
        log_text = "fixme:win: normal message\n"
        parser = LogParser()
        sections = parser.parse_text(log_text)
        issues = engine.analyze(sections)
        assert issues == []

    def test_analyze_with_empty_sections(self) -> None:
        """Engine should handle empty sections list."""
        engine = DiagnosticEngine([])
        issues = engine.analyze([])
        assert issues == []

    def test_analyze_with_multiple_patterns(self) -> None:
        """Engine should match against all patterns."""
        patterns = [
            DiagnosticPattern(
                name="missing_dll",
                description="Test",
                regex=r"err:module:import_dll.*Library\s+\S+\.dll",
                issue_type="missing_dll",
                severity="error",
                title="Missing DLL",
                suggestion="Install via winetricks",
            ),
            DiagnosticPattern(
                name="permission_denied",
                description="Test",
                regex=r"Permission denied",
                issue_type="permission_error",
                severity="error",
                title="Permission Error",
                suggestion="Check file permissions",
            ),
        ]
        engine = DiagnosticEngine(patterns)
        log_text = """err:module:import_dll: Library test.dll not found
Permission denied opening /path/to/file
fixme:win: normal message
"""
        parser = LogParser()
        sections = parser.parse_text(log_text)
        issues = engine.analyze(sections)
        assert len(issues) == 2
        types = {i.issue_type for i in issues}
        assert "missing_dll" in types
        assert "permission_error" in types

    def test_confidence_scoring(self) -> None:
        """Confidence should be between 0 and 1."""
        patterns = [
            DiagnosticPattern(
                name="test",
                description="Test",
                regex=r"error.*pattern",
                issue_type="test",
                severity="error",
                title="Test",
                suggestion="Test",
            ),
        ]
        engine = DiagnosticEngine(patterns)
        log_text = "this is an error pattern match\n"
        parser = LogParser()
        sections = parser.parse_text(log_text)
        issues = engine.analyze(sections)
        assert len(issues) == 1
        assert 0.0 <= issues[0].confidence <= 1.0

    def test_multiple_matches_same_pattern(self) -> None:
        """Multiple matches of same pattern should create multiple issues."""
        patterns = [
            DiagnosticPattern(
                name="missing_dll",
                description="Test",
                regex=r"err:module:import_dll.*Library\s+(\S+)\.dll",
                issue_type="missing_dll",
                severity="error",
                title="Missing DLL",
                suggestion="Install via winetricks",
            ),
        ]
        engine = DiagnosticEngine(patterns)
        log_text = """err:module:import_dll: Library d3dx9_43.dll not found
err:module:import_dll: Library xinput1_3.dll not found
"""
        parser = LogParser()
        sections = parser.parse_text(log_text)
        issues = engine.analyze(sections)
        assert len(issues) == 2
        # Each issue should reference a different DLL
        dlls = [i.title for i in issues]
        assert any("d3dx9_43" in dll for dll in dlls)
        assert any("xinput1_3" in dll for dll in dlls)
