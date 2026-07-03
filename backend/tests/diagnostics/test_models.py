"""Tests for diagnostics data models."""

from __future__ import annotations

from app.diagnostics.models import DiagnosticIssue, DiagnosticPattern, DiagnosticResult


class TestDiagnosticPattern:
    """Tests for DiagnosticPattern dataclass."""

    def test_create_pattern(self) -> None:
        """Create a pattern with basic fields."""
        pattern = DiagnosticPattern(
            name="missing_dll",
            description="Detects missing DLL errors in Wine logs",
            regex=r"err:module:import_dll.*Library\s+(\S+)\.dll",
            issue_type="missing_dll",
            severity="error",
            title="Missing DLL Detected",
            suggestion="Install the missing DLL via winetricks",
        )
        assert pattern.name == "missing_dll"
        assert pattern.issue_type == "missing_dll"
        assert pattern.severity == "error"

    def test_pattern_regex_compiles(self) -> None:
        """Pattern regex should compile successfully."""
        pattern = DiagnosticPattern(
            name="test",
            description="Test",
            regex=r"test.*pattern",
            issue_type="test",
            severity="info",
            title="Test",
            suggestion="Test suggestion",
        )
        import re
        compiled = re.compile(pattern.regex, re.IGNORECASE)
        assert compiled.search("This is a test pattern")
        assert not compiled.search("no match here")

    def test_all_fields_required(self) -> None:
        """All fields should be required (no defaults)."""
        import dataclasses
        fields = {f.name for f in dataclasses.fields(DiagnosticPattern)}
        expected = {"name", "description", "regex", "issue_type", "severity", "title", "suggestion"}
        assert fields == expected


class TestDiagnosticIssue:
    """Tests for DiagnosticIssue dataclass."""

    def test_create_issue(self) -> None:
        """Create an issue with all fields."""
        issue = DiagnosticIssue(
            issue_type="missing_dll",
            severity="error",
            title="Missing DLL: xinput1_3.dll",
            description="Wine cannot find xinput1_3.dll",
            suggestion="Install xinput via winetricks",
            log_lines=['err:module:import_dll: Library xinput1_3.dll'],
            confidence=0.95,
            pattern_name="missing_dll",
        )
        assert issue.confidence == 0.95
        assert len(issue.log_lines) == 1
        assert issue.pattern_name == "missing_dll"

    def test_issue_with_empty_log_lines(self) -> None:
        """Issue should accept empty log lines list."""
        issue = DiagnosticIssue(
            issue_type="test",
            severity="warning",
            title="Test",
            description="Desc",
            suggestion="Fix",
            log_lines=[],
            confidence=0.5,
            pattern_name="test",
        )
        assert issue.log_lines == []


class TestDiagnosticResult:
    """Tests for DiagnosticResult dataclass."""

    def test_create_result(self) -> None:
        """Create a result with issues."""
        issue = DiagnosticIssue(
            issue_type="missing_dll",
            severity="error",
            title="Missing DLL",
            description="DLL not found",
            suggestion="Install it",
            log_lines=["err:module:..."],
            confidence=0.95,
            pattern_name="missing_dll",
        )
        result = DiagnosticResult(
            issues=[issue],
            summary="Found 1 issue",
            log_path="/tmp/wine.log",
            runner="wine",
            log_line_count=100,
        )
        assert len(result.issues) == 1
        assert result.runner == "wine"
        assert result.log_line_count == 100

    def test_result_with_no_issues(self) -> None:
        """Result should handle empty issues list."""
        result = DiagnosticResult(
            issues=[],
            summary="No issues found",
            log_path=None,
            runner="native",
            log_line_count=0,
        )
        assert result.issues == []
        assert result.log_path is None
