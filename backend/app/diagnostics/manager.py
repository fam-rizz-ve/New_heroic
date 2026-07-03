"""DiagnosticsManager — orchestrates log analysis."""

from __future__ import annotations

import structlog

from app.diagnostics.engine import DiagnosticEngine
from app.diagnostics.models import DiagnosticIssue, DiagnosticPattern, DiagnosticResult
from app.diagnostics.parser import LogParser
from app.diagnostics.patterns import BUILTIN_PATTERNS

logger = structlog.get_logger(__name__)


def _build_summary(issues: list[DiagnosticIssue]) -> str:
    """Build a one-line summary from a list of issues."""
    if not issues:
        return "No issues detected"
    errors = sum(1 for i in issues if i.severity == "error")
    warnings = sum(1 for i in issues if i.severity == "warning")
    parts = []
    if errors:
        parts.append(f"{errors} error{'s' if errors != 1 else ''}")
    if warnings:
        parts.append(f"{warnings} warning{'s' if warnings != 1 else ''}")
    if parts:
        return f"Found {', '.join(parts)}"
    return f"Found {len(issues)} issue{'s' if len(issues) != 1 else ''}"


class DiagnosticsManager:
    """Manages diagnostic patterns and orchestrates log analysis.

    Follows the Manager/registry pattern used by RunnerManager,
    InstallerManager, and StoreManager elsewhere in the project.
    """

    def __init__(self) -> None:
        """Initialize with an empty pattern registry."""
        self._patterns: dict[str, DiagnosticPattern] = {}
        self._parser = LogParser()
        self._engine: DiagnosticEngine | None = None

    def register_pattern(self, pattern: DiagnosticPattern) -> None:
        """Register a diagnostic pattern.

        Args:
            pattern: The DiagnosticPattern to register.
                Replaces any existing pattern with the same name.
        """
        self._patterns[pattern.name] = pattern
        self._engine = None  # Invalidate cached engine
        logger.debug("Pattern registered", name=pattern.name)

    def list_patterns(self) -> list[DiagnosticPattern]:
        """List all registered patterns.

        Returns:
            A copy of the internal pattern list.
        """
        return list(self._patterns.values())

    def _get_engine(self) -> DiagnosticEngine:
        """Get or create the cached engine.

        Returns:
            A DiagnosticEngine instance with current patterns.
        """
        if self._engine is None:
            self._engine = DiagnosticEngine(list(self._patterns.values()))
        return self._engine

    def analyze_text(self, log_content: str, runner: str = "") -> DiagnosticResult:
        """Analyze raw log text.

        Args:
            log_content: Raw log content as a string.
            runner: Optional runner name for context (e.g. "wine", "native").

        Returns:
            A DiagnosticResult with detected issues.
        """
        sections = self._parser.parse_text(log_content)
        engine = self._get_engine()
        issues = engine.analyze(sections)
        line_count = sum(len(s.lines) for s in sections)

        return DiagnosticResult(
            issues=issues,
            summary=_build_summary(issues),
            log_path=None,
            runner=runner,
            log_line_count=line_count,
        )

    def analyze_file(self, log_path: str, runner: str = "") -> DiagnosticResult:
        """Analyze a log file.

        Args:
            log_path: Path to the log file.
            runner: Optional runner name for context (e.g. "wine", "native").

        Returns:
            A DiagnosticResult with detected issues.

        Raises:
            FileNotFoundError: If the log file does not exist.
        """
        sections = self._parser.parse_file(log_path)
        engine = self._get_engine()
        issues = engine.analyze(sections)
        line_count = sum(len(s.lines) for s in sections)

        return DiagnosticResult(
            issues=issues,
            summary=_build_summary(issues),
            log_path=log_path,
            runner=runner,
            log_line_count=line_count,
        )

    @classmethod
    def create_default(cls) -> DiagnosticsManager:
        """Create a DiagnosticsManager with all built-in patterns.

        Returns:
            A configured DiagnosticsManager instance.
        """
        manager = cls()
        for pattern in BUILTIN_PATTERNS:
            manager.register_pattern(pattern)
        logger.info("Default diagnostics patterns registered", count=len(BUILTIN_PATTERNS))
        return manager
