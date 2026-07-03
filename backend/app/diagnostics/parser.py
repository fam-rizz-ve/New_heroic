"""Log parser for reading and structuring log files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class LogSection:
    """A section of a log file."""

    name: str
    lines: list[str] = field(default_factory=list)
    line_numbers: list[int] = field(default_factory=list)


class LogParser:
    """Parses log content into structured sections.

    For now, returns a single section with all lines.
    Future versions can split by Wine debug channels.
    """

    def parse_text(self, content: str) -> list[LogSection]:
        """Parse raw log text into sections.

        Args:
            content: Raw log text to parse.

        Returns:
            List of LogSection objects. Empty list if content is empty or whitespace only.
        """
        if not content or not content.strip():
            return []

        lines = content.splitlines()
        section = LogSection(name="main")
        for i, line in enumerate(lines, 1):
            if line.strip():
                section.lines.append(line.strip())
                section.line_numbers.append(i)

        logger.debug("Parsed log text", line_count=len(section.lines))
        return [section] if section.lines else []

    def parse_file(self, path: str) -> list[LogSection]:
        """Parse a log file into sections.

        Args:
            path: Path to the log file.

        Returns:
            List of LogSection objects.

        Raises:
            FileNotFoundError: If the log file does not exist.
        """
        file_path = Path(path)
        if not file_path.exists():
            logger.error("Log file not found", path=path)
            raise FileNotFoundError(f"Log file not found: {path}")

        content = file_path.read_text(encoding="utf-8", errors="replace")
        logger.info("Log file read", path=path, size=len(content))
        return self.parse_text(content)
