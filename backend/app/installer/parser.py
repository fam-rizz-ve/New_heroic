"""YAML parser for game installer manifests."""

from __future__ import annotations

from pathlib import Path

import structlog
import yaml

from app.installer.models import InstallerFile, InstallerManifest, InstallerStep

logger = structlog.get_logger(__name__)


class InstallerParseError(Exception):
    """Raised when an installer YAML file cannot be parsed."""

    pass


def parse_installer(yaml_content: str) -> InstallerManifest:
    """Parse a YAML installer string into an InstallerManifest."""
    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise InstallerParseError(f"Invalid YAML: {e}")

    if not isinstance(data, dict):
        raise InstallerParseError("Installer YAML must be a mapping")

    # Parse required fields
    name = data.get("name", "")
    if not name:
        raise InstallerParseError("Installer must have a 'name' field")

    game_slug = data.get("game_slug", "")
    if not game_slug:
        raise InstallerParseError("Installer must have a 'game_slug' field")

    version = str(data.get("version", "1.0"))

    # Parse files
    files: list[InstallerFile] = []
    raw_files = data.get("files", {})
    if isinstance(raw_files, dict):
        for file_name, url in raw_files.items():
            files.append(InstallerFile(name=str(file_name), url=str(url)))

    # Parse installer steps
    steps: list[InstallerStep] = []
    raw_installer = data.get("installer", [])
    if isinstance(raw_installer, list):
        for item in raw_installer:
            if isinstance(item, dict):
                for action, config in item.items():
                    if isinstance(config, dict):
                        steps.append(
                            InstallerStep(
                                action=action,
                                description=config.pop("description", ""),
                                config=config,
                            )
                        )
                    elif isinstance(config, str):
                        steps.append(
                            InstallerStep(
                                action=action,
                                description="",
                                config={"value": config},
                            )
                        )

    manifest = InstallerManifest(
        name=name,
        game_slug=game_slug,
        version=version,
        runner=data.get("runner", "wine"),
        year=str(data.get("year", "")),
        description=data.get("description", ""),
        notes=data.get("notes", ""),
        files=files,
        steps=steps,
    )

    logger.info(
        "Installer parsed",
        name=manifest.name,
        steps=len(manifest.steps),
        files=len(manifest.files),
    )

    return manifest


def load_installer_file(path: Path) -> InstallerManifest:
    """Load and parse an installer YAML file from disk."""
    logger.debug("Loading installer file", path=str(path))
    content = path.read_text()
    return parse_installer(content)
