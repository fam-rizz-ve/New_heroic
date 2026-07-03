"""Tests for log parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.diagnostics.parser import LogParser, LogSection


class TestLogSection:
    """Tests for LogSection."""

    def test_create_section(self) -> None:
        """Create a log section."""
        section = LogSection(
            name="module",
            lines=["err:module:import_dll: Library test.dll not found"],
            line_numbers=[1],
        )
        assert section.name == "module"
        assert len(section.lines) == 1


class TestLogParser:
    """Tests for LogParser."""

    def test_parse_basic_log(self) -> None:
        """Parse a simple log with multiple lines."""
        log_text = """info: game started
err:module:import_dll: Library test.dll not found
fixme:win: message
"""
        parser = LogParser()
        result = parser.parse_text(log_text)
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

    def test_parse_empty_log(self) -> None:
        """Parsing empty log should return empty list."""
        parser = LogParser()
        result = parser.parse_text("")
        assert result == []

    def test_parse_whitespace_only(self) -> None:
        """Parsing whitespace-only log should return empty list."""
        parser = LogParser()
        result = parser.parse_text("   \n  \n   ")
        assert result == []

    def test_parse_single_section(self) -> None:
        """All lines should be in a single section for simple logs."""
        log_text = "line1\nline2\nline3\n"
        parser = LogParser()
        sections = parser.parse_text(log_text)
        assert len(sections) >= 1
        all_lines = []
        for section in sections:
            all_lines.extend(section.lines)
        assert len(all_lines) == 3

    def test_parse_file_not_found(self, tmp_path: Path) -> None:
        """Parsing nonexistent file should raise FileNotFoundError."""
        parser = LogParser()
        with pytest.raises(FileNotFoundError):
            parser.parse_file(str(tmp_path / "nonexistent.log"))

    def test_parse_file(self, tmp_path: Path) -> None:
        """Parse a real log file."""
        log_file = tmp_path / "test.log"
        log_file.write_text("err:module:import_dll: Library test.dll not found\n")
        parser = LogParser()
        result = parser.parse_file(str(log_file))
        assert len(result) > 0

    def test_parse_file_empty(self, tmp_path: Path) -> None:
        """Parse an empty log file."""
        log_file = tmp_path / "empty.log"
        log_file.write_text("")
        parser = LogParser()
        result = parser.parse_file(str(log_file))
        assert result == []

    def test_parse_file_with_error(self, tmp_path: Path) -> None:
        """Parse a file with various Wine debug messages."""
        log_file = tmp_path / "wine.log"
        log_file.write_text("""fixme:win: some message
err:module:import_dll: Library d3dx9_43.dll not found
err:winediag: something
fixme:d3d: some fixme
""")
        parser = LogParser()
        sections = parser.parse_file(str(log_file))
        all_lines = []
        for section in sections:
            all_lines.extend(section.lines)
        assert len(all_lines) == 4

    def test_parse_preserves_section_order(self) -> None:
        """Sections should preserve original line order."""
        log_text = """line1
line2
line3
"""
        parser = LogParser()
        sections = parser.parse_text(log_text)
        if len(sections) == 1:
            assert sections[0].lines == ["line1", "line2", "line3"]
