"""Base classes and types for store integrations."""

from __future__ import annotations

import asyncio
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import structlog


@dataclass
class StoreGame:
    """Game metadata from a store."""

    store_id: str
    title: str
    description: str = ""
    cover_art_url: str = ""
    developer: str = ""
    publisher: str = ""
    release_date: str | None = None
    genres: list[str] = field(default_factory=list)


@dataclass
class StoreCredentials:
    """Authentication credentials for a store."""

    token: str
    username: str | None = None
    expires_at: str | None = None


class StoreBase(ABC):
    """Abstract base for store integrations.

    Wraps a CLI tool as a subprocess. Subclasses define:
    - name, display_name
    - _cli_name (the executable name)
    - How to parse CLI output
    """

    name: str = ""
    display_name: str = ""
    _cli_name: str = ""
    logger: structlog.stdlib.BoundLogger

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        cls.logger = structlog.get_logger(f"app.stores.{cls.__name__}")

    async def _run_command(
        self, args: list[str], input_data: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        """Run a CLI command and return the result.

        Override in tests to mock subprocess calls.

        Raises:
            RuntimeError: If the CLI tool fails or is not found.
        """
        self.logger.info("Running CLI command", cli=self._cli_name, args=args)
        try:
            proc = await asyncio.create_subprocess_exec(
                self._cli_name,
                *args,
                stdin=asyncio.subprocess.PIPE if input_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            self.logger.error("CLI tool not found", cli=self._cli_name)
            raise RuntimeError(
                f"{self._cli_name} is not installed or not found on PATH"
            )
        stdout, stderr = await proc.communicate(
            input=input_data.encode() if input_data else None
        )
        if proc.returncode != 0:
            self.logger.error(
                "CLI command failed",
                cli=self._cli_name,
                returncode=proc.returncode,
                stderr=stderr.decode().strip(),
            )
            raise RuntimeError(
                f"{self._cli_name} failed (exit {proc.returncode}): "
                f"{stderr.decode().strip()}"
            )
        self.logger.debug(
            "CLI command succeeded",
            cli=self._cli_name,
            returncode=proc.returncode,
        )
        return subprocess.CompletedProcess(
            args=args,
            returncode=proc.returncode,
            stdout=stdout.decode(),
            stderr=stderr.decode(),
        )

    async def check_installed(self) -> bool:
        """Check if the CLI tool is available on PATH."""
        self.logger.debug("Checking if CLI is installed", cli=self._cli_name)
        proc = await asyncio.create_subprocess_exec(
            "which",
            self._cli_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        return proc.returncode == 0

    @abstractmethod
    async def authenticate(self, code: str) -> StoreCredentials:
        """Authenticate with the store using an auth code."""
        ...

    @abstractmethod
    async def is_authenticated(self) -> bool:
        """Check if we have valid credentials."""
        ...

    @abstractmethod
    async def list_games(self) -> list[StoreGame]:
        """List all games in the user's library."""
        ...

    @abstractmethod
    async def get_game_details(self, store_id: str) -> StoreGame:
        """Get detailed metadata for a specific game."""
        ...

    @abstractmethod
    async def install_game(self, store_id: str, install_path: str) -> None:
        """Download and install a game."""
        ...

    @abstractmethod
    async def get_auth_url(self) -> str:
        """Return the OAuth login URL for this store.

        Returns:
            The URL the user should open in their browser to start OAuth.
        """
        ...

    @abstractmethod
    async def get_auth_instructions(self) -> str:
        """Return human-readable login instructions for this store.

        Returns:
            Instructions explaining how the user should log in
            (e.g., what to do after opening the auth URL).
        """
        ...

    async def get_auth_url_for_callback(self, callback_url: str) -> str:
        """Return the OAuth login URL with a specific callback redirect.

        Subclasses should override this if the OAuth provider supports
        custom redirect URIs (e.g., Epic, GOG).

        Args:
            callback_url: The URL the OAuth provider should redirect to
                         (e.g., http://127.0.0.1:{port}/callback).

        Returns:
            The full OAuth URL with the callback embedded.
        """
        # Default: return the standard auth URL (stores that don't support
        # custom callbacks fall back to manual code entry).
        return await self.get_auth_url()

    async def start_browser_auth(self) -> StoreCredentials:
        """Start browser-based OAuth authentication.

        Default implementation raises NotImplementedError.
        Override in subclasses that support automatic auth
        (e.g., Epic uses Legendary's built-in auth, GOG uses a
        local callback server).

        Raises:
            NotImplementedError: If auto auth is not supported.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support automatic browser "
            f"authentication. Use the manual auth flow instead."
        )
