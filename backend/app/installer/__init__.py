"""Game installer engine — YAML-based installation system.

Inspired by Lutris installer format. Supports downloading, extracting,
Wine configuration, and step-by-step game installation.
"""

from app.installer.executor import InstallExecutor
from app.installer.manager import InstallerManager
from app.installer.models import InstallerFile, InstallerManifest, InstallerStep
from app.installer.parser import InstallerParseError, load_installer_file, parse_installer

__all__ = [
    "InstallerFile",
    "InstallerManifest",
    "InstallerStep",
    "InstallerParseError",
    "parse_installer",
    "load_installer_file",
    "InstallExecutor",
    "InstallerManager",
]
