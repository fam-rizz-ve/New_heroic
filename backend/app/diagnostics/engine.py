"""Core diagnostic detection engine."""

from __future__ import annotations

import re
from collections.abc import Sequence

import structlog

from app.diagnostics.models import DiagnosticIssue, DiagnosticPattern
from app.diagnostics.parser import LogSection

logger = structlog.get_logger(__name__)

# Base confidence for a pattern match
_BASE_CONFIDENCE = 0.8
# Confidence boost for each additional matching line
_LINE_BOOST = 0.05
# Maximum confidence cap
_MAX_CONFIDENCE = 1.0


class DiagnosticEngine:
    """Core engine that analyzes log sections and detects issues.

    Takes a list of DiagnosticPattern objects and runs them
    against parsed log sections to produce DiagnosticIssues.
    """

    def __init__(self, patterns: Sequence[DiagnosticPattern]) -> None:
        """Initialize the engine with patterns.

        Args:
            patterns: List of DiagnosticPattern objects to match against.
        """
        self._patterns = {p.name: p for p in patterns}

    def analyze(self, sections: list[LogSection]) -> list[DiagnosticIssue]:
        """Analyze log sections and detect issues.

        Args:
            sections: Parsed log sections to analyze.

        Returns:
            List of detected DiagnosticIssue objects (empty list if none found).
        """
        if not sections:
            return []

        issues: list[DiagnosticIssue] = []

        for pattern in self._patterns.values():
            compiled = re.compile(pattern.regex, re.IGNORECASE)
            for section in sections:
                for line in section.lines:
                    if not compiled.search(line):
                        continue

                    # Determine title with the matched line for context
                    title = pattern.title
                    if "DLL" in pattern.title:
                        dll_match = re.search(r'Library\s+(\S+)', line)
                        if dll_match:
                            title = f"Missing DLL: {dll_match.group(1)}"

                    issues.append(
                        DiagnosticIssue(
                            issue_type=pattern.issue_type,
                            severity=pattern.severity,
                            title=title,
                            description=(
                                f"Pattern '{pattern.name}' matched"
                                f" in {section.name} section"
                            ),
                            suggestion=pattern.suggestion,
                            log_lines=[line],
                            confidence=_BASE_CONFIDENCE,
                            pattern_name=pattern.name,
                        )
                    )

        issues.sort(key=lambda i: i.confidence, reverse=True)
        logger.info(
            "Analysis complete",
            sections=len(sections),
            patterns=len(self._patterns),
            issues_found=len(issues),
        )
        return issues
