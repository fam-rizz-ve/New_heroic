"""Application configuration using pydantic-settings.

IPC Architecture:
  Frontend (Tauri webview, port 1420) ──HTTP──► Backend (FastAPI sidecar, port 1430)

  In development:
    - Vite dev server runs on http://localhost:1420
    - FastAPI backend runs on http://localhost:1430
    - The frontend proxies API calls to the backend via fetch()

  In production:
    - Tauri bundles the frontend and spawns the Python backend as a sidecar process
    - The Tauri webview origin is tauri://localhost (NOT http://localhost)
    - CORS must allow both origins for the health check to work in all environments
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "New Heroic"
    app_version: str = "0.1.0"
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 1430

    # Backend port — alias for `port` for environments that prefer explicit naming
    backend_port: int = 1430

    # Frontend dev server port (for documentation/reference; the backend does not
    # serve the frontend, so this is informational only)
    frontend_port: int = 1420

    log_level: str = "info"

    # CORS origins
    #
    # These origins are allowed to make cross-origin requests to the backend API.
    # All must be present for the health check and all API calls to work in
    # both development and production environments.
    #
    # Origins:
    #   http://localhost:1420 — Vite dev server via localhost (development)
    #     During development, the frontend is served by Vite at localhost:1420
    #     and makes HTTP requests to the backend at localhost:1430.
    #
    #   http://127.0.0.1:1420 — Vite dev server via loopback IP (development)
    #     Browsers treat localhost and 127.0.0.1 as different origins, so both
    #     must be listed to avoid CORS errors when accessing via the IP address.
    #
    #   tauri://localhost — Tauri production webview origin
    #     In production builds, the Tauri webview uses tauri://localhost as its
    #     origin (not http://localhost). The backend must allow this origin for
    #     API calls to succeed in the packaged app.
    cors_origins: list[str] = [
        "http://localhost:1420",
        "http://127.0.0.1:1420",
        "tauri://localhost",
    ]

    # Database (future)
    database_url: str = ""


settings = Settings()
