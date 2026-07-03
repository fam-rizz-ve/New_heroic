"""Store integrations for game sources (Epic, GOG, etc.)."""

from app.stores.base import StoreBase, StoreCredentials, StoreGame
from app.stores.epic import EpicStore
from app.stores.gog import GOGStore
from app.stores.manager import StoreManager

__all__ = [
    "StoreBase",
    "StoreCredentials",
    "StoreGame",
    "EpicStore",
    "GOGStore",
    "StoreManager",
]
