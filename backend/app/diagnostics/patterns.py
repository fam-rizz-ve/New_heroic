"""Built-in diagnostic patterns for log analysis."""

from __future__ import annotations

from app.diagnostics.models import DiagnosticPattern

BUILTIN_PATTERNS: list[DiagnosticPattern] = [
    DiagnosticPattern(
        name="missing_dll",
        description="Detects missing DLL errors in Wine logs",
        regex=r"err:module:import_dll.*Library\s+\S+\.dll",
        issue_type="missing_dll",
        severity="error",
        title="Missing DLL Detected",
        suggestion="Install the missing DLL via winetricks. "
        'Run: `winetricks <dll_name>` or check the game\'s '
        "redistributables (DirectX, VC++).",
    ),
    DiagnosticPattern(
        name="vulkan_not_supported",
        description="Detects Vulkan/GPU issues",
        regex=r"vulkan.*not\s+supported|VK_ERROR|vulkan.*failed",
        issue_type="vulkan_error",
        severity="error",
        title="Vulkan/GPU Error",
        suggestion="Update your GPU drivers. Ensure Vulkan libraries are installed. "
        "On Linux: `sudo apt install mesa-vulkan-drivers` or equivalent "
        "for your distribution.",
    ),
    DiagnosticPattern(
        name="permission_denied",
        description="Detects file permission errors",
        regex=r"Permission\s+denied|EACCES",
        issue_type="permission_error",
        severity="error",
        title="Permission Denied",
        suggestion="Check file permissions on the game directory. "
        "Run: `chmod -R u+w <game_dir>` or ensure the directory "
        "is owned by your user.",
    ),
    DiagnosticPattern(
        name="wrong_elf_class",
        description="Detects Wine architecture mismatch",
        regex=r"wrong\s+ELF\s+class",
        issue_type="wine_architecture",
        severity="error",
        title="Wine Architecture Mismatch",
        suggestion="Set WINEARCH to match the game binary: "
        "For 64-bit games: `export WINEARCH=win64`. "
        "For 32-bit games: `export WINEARCH=win32`. "
        "Create a new WINEPREFIX with the correct architecture.",
    ),
    DiagnosticPattern(
        name="dxvk_error",
        description="Detects DXVK/VKD3D errors",
        regex=r"DXVK:.*(?:failed|error|FIXME)",
        issue_type="dxvk_error",
        severity="warning",
        title="DXVK/VKD3D Error",
        suggestion="Try a different DXVK or VKD3D version. "
        "Disable DXVK/VKD3D in game settings if the issue persists. "
        "Ensure your GPU drivers support Vulkan 1.3+.",
    ),
    DiagnosticPattern(
        name="out_of_memory",
        description="Detects out of memory errors",
        regex=r"Cannot\s+allocate\s+memory|Out\s+of\s+memory",
        issue_type="memory_error",
        severity="error",
        title="Out of Memory",
        suggestion="Free up system memory by closing other applications. "
        "Increase swap space: `sudo fallocate -l 8G /swapfile`. "
        "Consider adding more RAM to your system.",
    ),
    DiagnosticPattern(
        name="file_not_found",
        description="Detects missing game files",
        regex=r"No\s+such\s+file\s+or\s+directory\s+\S+\.(?:exe|dll)",
        issue_type="file_not_found",
        severity="error",
        title="Game File Not Found",
        suggestion="Verify the game installation. "
        "Reinstall the game or check if files were moved/deleted. "
        "If using a Wine prefix, ensure the game is installed "
        "in the correct prefix.",
    ),
    DiagnosticPattern(
        name="wine_prefix_error",
        description="Detects Wine prefix issues",
        regex=r"wine:.*WINEPREFIX|wineprefixcreate\s+failed",
        issue_type="wine_prefix_error",
        severity="error",
        title="Wine Prefix Error",
        suggestion="Check that your WINEPREFIX is valid and accessible. "
        "Try recreating the prefix: `rm -rf ~/.wine && winecfg`. "
        "Ensure the prefix path exists and has correct permissions.",
    ),
]


def get_patterns_by_type(issue_type: str) -> list[DiagnosticPattern]:
    """Get all patterns matching a specific issue type."""
    return [p for p in BUILTIN_PATTERNS if p.issue_type == issue_type]
