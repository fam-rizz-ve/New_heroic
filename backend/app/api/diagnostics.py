"""API endpoints for the Diagnostics Engine."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status

from app.diagnostics.manager import DiagnosticsManager
from app.schemas.diagnostics import (
    AnalyzeFileRequest,
    AnalyzeRequest,
    DiagnosticIssueSchema,
    DiagnosticResultSchema,
    PatternSchema,
)

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])

_manager: DiagnosticsManager | None = None


def get_diagnostics_manager() -> DiagnosticsManager:
    """Dependency: get the DiagnosticsManager singleton."""
    global _manager
    if _manager is None:
        _manager = DiagnosticsManager.create_default()
    return _manager


@router.post("/analyze", response_model=DiagnosticResultSchema)
async def analyze_log(
    request: AnalyzeRequest,
    manager: DiagnosticsManager = Depends(get_diagnostics_manager),
) -> DiagnosticResultSchema:
    """Analyze raw log content for known error patterns.

    Args:
        request: AnalyzeRequest with log_content and optional runner context.

    Returns:
        DiagnosticResultSchema with detected issues and summary.
    """
    result = manager.analyze_text(
        log_content=request.log_content,
        runner=request.runner,
    )
    return DiagnosticResultSchema(
        issues=[DiagnosticIssueSchema(**asdict(i)) for i in result.issues],
        summary=result.summary,
        log_path=result.log_path,
        runner=result.runner,
        log_line_count=result.log_line_count,
    )


@router.post("/analyze-file", response_model=DiagnosticResultSchema)
async def analyze_log_file(
    request: AnalyzeFileRequest,
    manager: DiagnosticsManager = Depends(get_diagnostics_manager),
) -> DiagnosticResultSchema:
    """Analyze a log file for known error patterns.

    Args:
        request: AnalyzeFileRequest with log_path and optional runner context.

    Returns:
        DiagnosticResultSchema with detected issues and summary.

    Raises:
        HTTPException 404: If the log file does not exist.
        HTTPException 500: If the file cannot be read.
    """
    try:
        result = manager.analyze_file(
            log_path=request.log_path,
            runner=request.runner,
        )
        return DiagnosticResultSchema(
            issues=[DiagnosticIssueSchema(**asdict(i)) for i in result.issues],
            summary=result.summary,
            log_path=result.log_path,
            runner=result.runner,
            log_line_count=result.log_line_count,
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except (OSError, PermissionError) as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cannot read log file: {e}",
        )


@router.get("/patterns", response_model=list[PatternSchema])
async def list_patterns(
    manager: DiagnosticsManager = Depends(get_diagnostics_manager),
) -> list[PatternSchema]:
    """List all available diagnostic patterns.

    Returns:
        A list of PatternSchema with pattern definitions.
    """
    patterns = manager.list_patterns()
    return [
        PatternSchema(
            name=p.name,
            description=p.description,
            issue_type=p.issue_type,
            severity=p.severity,
            title=p.title,
            suggestion=p.suggestion,
        )
        for p in patterns
    ]
