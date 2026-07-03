"""Pydantic schemas for diagnostics API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DiagnosticIssueSchema(BaseModel):
    """A single issue detected during log analysis."""

    issue_type: str
    severity: str
    title: str
    description: str
    suggestion: str
    log_lines: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    pattern_name: str = ""


class DiagnosticResultSchema(BaseModel):
    """Result of a diagnostic analysis."""

    issues: list[DiagnosticIssueSchema] = Field(default_factory=list)
    summary: str = ""
    log_path: str | None = None
    runner: str = ""
    log_line_count: int = 0


class AnalyzeRequest(BaseModel):
    """Request to analyze log content."""

    log_content: str = Field(..., description="Raw log content to analyze")
    runner: str = Field(..., description="Runner context (e.g. 'wine', 'native')")


class AnalyzeFileRequest(BaseModel):
    """Request to analyze a log file."""

    log_path: str = Field(..., min_length=1, description="Path to the log file")
    runner: str = Field(default="", description="Runner context (e.g. 'wine', 'native')")


class PatternSchema(BaseModel):
    """A diagnostic pattern definition."""

    name: str
    description: str
    issue_type: str
    severity: str
    title: str
    suggestion: str
