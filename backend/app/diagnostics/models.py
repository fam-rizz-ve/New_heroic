"""Data models for the Diagnostics Engine."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DiagnosticPattern:
    """A pattern to detect in log files."""

    name: str
    description: str
    regex: str
    issue_type: str
    severity: str
    title: str
    suggestion: str


@dataclass
class DiagnosticIssue:
    """A single issue detected during log analysis."""

    issue_type: str
    severity: str
    title: str
    description: str
    suggestion: str
    log_lines: list[str] = field(default_factory=list)
    confidence: float = 0.0
    pattern_name: str = ""


@dataclass
class DiagnosticResult:
    """Complete result of a diagnostic run."""

    issues: list[DiagnosticIssue] = field(default_factory=list)
    summary: str = ""
    log_path: str | None = None
    runner: str = ""
    log_line_count: int = 0
