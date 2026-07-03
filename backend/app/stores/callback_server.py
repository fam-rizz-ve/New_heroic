"""Local HTTP callback server for OAuth authentication.

Starts a temporary HTTP server on a random port to capture OAuth redirects.
"""

from __future__ import annotations

import asyncio
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler that captures OAuth callback parameters."""

    def do_GET(self) -> None:
        """Extract auth code from query parameters."""
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        code_list = (
            params.get("authorizationCode")
            or params.get("code")
            or params.get("sid")
        )
        code = code_list[0] if code_list else None

        if code:
            self.server.callback_code = code  # type: ignore[attr-defined]
            self._respond(
                200,
                "Authentication successful! You can close this window.",
            )
        else:
            self.server.callback_code = None  # type: ignore[attr-defined]
            self._respond(
                400,
                "Authentication failed. No authorization code found "
                "in the redirect URL.",
            )

    def _respond(self, status: int, message: str) -> None:
        """Send an HTML response to the browser."""
        self.send_response(status)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        heading_color = "#34d399" if status == 200 else "#f87171"
        icon = "&#x2705; Success!" if status == 200 else "&#x274c; Error"
        html = (
            "<!DOCTYPE html>"
            "<html>"
            "<head>"
            "<meta charset='utf-8'>"
            "<title>New Heroic - Auth</title>"
            "<style>"
            "body{font-family:sans-serif;display:flex;justify-content:center;"
            "align-items:center;height:100vh;margin:0;background:#18181b;"
            "color:#e4e4e7;text-align:center}"
            ".card{background:#27272a;padding:2rem;border-radius:12px;"
            "max-width:400px}"
            f"h1{{color:{heading_color}}}"
            "p{color:#a1a1aa}"
            "</style>"
            "</head>"
            "<body>"
            "<div class='card'>"
            f"<h1>{icon}</h1>"
            f"<p>{message}</p>"
            "<p style='font-size:12px;margin-top:20px'>"
            "You can close this window."
            "</p>"
            "</div>"
            "</body>"
            "</html>"
        )
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format: str, *args: object) -> None:
        """Suppress HTTP server logs."""
        pass


class CallbackServer:
    """Local HTTP server to capture OAuth callback.

    Usage:
        server = CallbackServer()
        server.start()
        print(server.auth_url)  # URL for the OAuth provider
        code = await server.wait_for_code(timeout=120)
        server.stop()
    """

    def __init__(self, host: str = "127.0.0.1") -> None:
        self.host = host
        self._server = HTTPServer((host, 0), CallbackHandler)
        self._server.callback_code = None  # type: ignore[attr-defined]
        self._thread: Thread | None = None

    @property
    def port(self) -> int:
        """The port the server is listening on."""
        return self._server.server_address[1]

    def start(self) -> None:
        """Start the HTTP server in a daemon thread."""
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the HTTP server."""
        self._server.shutdown()
        if self._thread:
            self._thread.join(timeout=2)

    async def wait_for_code(self, timeout: int = 120) -> str:
        """Wait for the OAuth callback to arrive.

        Args:
            timeout: Maximum seconds to wait.

        Returns:
            The authorization code from the callback.

        Raises:
            TimeoutError: If no callback received within timeout.
        """
        loop = asyncio.get_event_loop()
        start = loop.time()
        while self._server.callback_code is None:  # type: ignore[attr-defined]
            await asyncio.sleep(0.1)
            if loop.time() - start > timeout:
                raise TimeoutError(
                    "Authentication timed out after 120 seconds. "
                    "Please try again.",
                )
        code: str = self._server.callback_code  # type: ignore[attr-defined]
        return code

    def open_browser(self, url: str) -> None:
        """Open the given URL in the system browser."""
        webbrowser.open(url)
