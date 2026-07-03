"""Domain enumerations for the game library."""

from enum import StrEnum


class StoreSource(StrEnum):
    """Which store a game comes from."""

    EPIC = "epic"
    GOG = "gog"
    STEAM = "steam"
    ITCH = "itch"
    LOCAL = "local"  # Manually added / imported


class RunnerType(StrEnum):
    """Which runner/launcher a game uses."""

    WINE = "wine"
    PROTON = "proton"
    PROTON_GE = "proton_ge"
    NATIVE = "native"


class GameStatus(StrEnum):
    """Current installation/run status of a game."""

    NOT_INSTALLED = "not_installed"
    INSTALLING = "installing"
    INSTALLED = "installed"
    RUNNING = "running"
    ERROR = "error"
