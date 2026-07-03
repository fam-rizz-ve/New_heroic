"""Tests for diagnostic pattern definitions."""

from __future__ import annotations

import re

import pytest

from app.diagnostics.patterns import BUILTIN_PATTERNS, get_patterns_by_type


class TestBuiltinPatterns:
    """Tests for built-in diagnostic patterns."""

    def test_all_patterns_have_unique_names(self) -> None:
        """All built-in patterns should have unique names."""
        names = [p.name for p in BUILTIN_PATTERNS]
        assert len(names) == len(set(names))

    def test_all_patterns_have_valid_severity(self) -> None:
        """All patterns should have valid severity levels."""
        valid = {"error", "warning", "info"}
        for p in BUILTIN_PATTERNS:
            assert p.severity in valid, f"Pattern '{p.name}' has invalid severity '{p.severity}'"

    def test_builtin_patterns_not_empty(self) -> None:
        """There should be at least one built-in pattern."""
        assert len(BUILTIN_PATTERNS) > 0

    def test_get_patterns_by_type(self) -> None:
        """get_patterns_by_type should filter correctly."""
        dll_patterns = get_patterns_by_type("missing_dll")
        for p in dll_patterns:
            assert p.issue_type == "missing_dll"

    def test_get_patterns_by_type_nonexistent(self) -> None:
        """Should return empty list for nonexistent type."""
        assert get_patterns_by_type("nonexistent") == []

    def test_missing_dll_pattern(self) -> None:
        """Test missing_dll pattern matches Wine DLL errors."""
        pattern = next(p for p in BUILTIN_PATTERNS if p.name == "missing_dll")
        compiled = re.compile(pattern.regex, re.IGNORECASE)
        assert compiled.search('err:module:import_dll: Library xinput1_3.dll not found')
        assert compiled.search('err:module:import_dll: Library d3dx9_43.dll (file missing)')
        assert not compiled.search('fixme:module: typical message')

    def test_vulkan_pattern(self) -> None:
        """Test vulkan_not_supported pattern."""
        pattern = next(p for p in BUILTIN_PATTERNS if p.name == "vulkan_not_supported")
        compiled = re.compile(pattern.regex, re.IGNORECASE)
        assert compiled.search('vulkan is not supported')
        assert compiled.search('VK_ERROR_INCOMPATIBLE_DRIVER')
        assert compiled.search('VK_ERROR_DEVICE_LOST')
        assert not compiled.search('normal log message')

    def test_permission_pattern(self) -> None:
        """Test permission_denied pattern."""
        pattern = next(p for p in BUILTIN_PATTERNS if p.name == "permission_denied")
        compiled = re.compile(pattern.regex, re.IGNORECASE)
        assert compiled.search('Permission denied')
        assert compiled.search('EACCES error opening file')
        assert not compiled.search('normal operation')

    def test_wrong_elf_class_pattern(self) -> None:
        """Test wrong_elf_class pattern."""
        pattern = next(p for p in BUILTIN_PATTERNS if p.name == "wrong_elf_class")
        compiled = re.compile(pattern.regex, re.IGNORECASE)
        assert compiled.search('wrong ELF class')
        assert not compiled.search('correct ELF class')

    def test_dxvk_error_pattern(self) -> None:
        """Test dxvk_error pattern."""
        pattern = next(p for p in BUILTIN_PATTERNS if p.name == "dxvk_error")
        compiled = re.compile(pattern.regex, re.IGNORECASE)
        assert compiled.search('DXVK: failed to create pipeline')
        assert compiled.search('DXVK: error occurred')
        assert not compiled.search('DXVK: info message')

    def test_out_of_memory_pattern(self) -> None:
        """Test out_of_memory pattern."""
        pattern = next(p for p in BUILTIN_PATTERNS if p.name == "out_of_memory")
        compiled = re.compile(pattern.regex, re.IGNORECASE)
        assert compiled.search('Cannot allocate memory')
        assert not compiled.search('normal allocation')

    def test_file_not_found_pattern(self) -> None:
        """Test file_not_found pattern for game files."""
        pattern = next(p for p in BUILTIN_PATTERNS if p.name == "file_not_found")
        compiled = re.compile(pattern.regex, re.IGNORECASE)
        assert compiled.search('No such file or directory game.exe')
        assert compiled.search('No such file or directory xinput1_3.dll')
        assert not compiled.search('No such file or directory readme.txt')
        assert not compiled.search('Permission denied opening file')

    def test_wine_prefix_error_pattern(self) -> None:
        """Test wine_prefix_error pattern."""
        pattern = next(p for p in BUILTIN_PATTERNS if p.name == "wine_prefix_error")
        compiled = re.compile(pattern.regex, re.IGNORECASE)
        assert compiled.search('wine: WINEPREFIX /tmp/wine/ does not exist')
        assert compiled.search('wineprefixcreate failed')
        assert not compiled.search('normal wine operation')

    def test_all_patterns_have_real_regex(self) -> None:
        """All patterns should have non-empty, compilable regex."""
        import re
        for p in BUILTIN_PATTERNS:
            try:
                re.compile(p.regex, re.IGNORECASE)
            except re.error as e:
                pytest.fail(f"Pattern '{p.name}' has invalid regex: {e}")

    def test_all_patterns_have_suggestions(self) -> None:
        """All patterns should have non-empty suggestions."""
        for p in BUILTIN_PATTERNS:
            assert p.suggestion.strip(), f"Pattern '{p.name}' has empty suggestion"
