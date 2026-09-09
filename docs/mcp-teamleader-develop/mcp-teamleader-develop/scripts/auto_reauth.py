"""
Teamleader OAuth Reauthentication Script

This script runs in a separate process from the MCP.

Responsibilities:
- Open browser for OAuth authorization
- Capture callback using local HTTP server
- Exchange authorization code for tokens
- Persist tokens in .env
- Update lifecycle state
- Restart Claude Desktop
- Terminate itself cleanly

This script must remain independent from MCP business logic.
"""

import os
import sys
import time
import webbrowser
import subprocess
import threading
import requests

from pathlib import Path
from datetime import datetime, timedelta, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv, set_key


# ==========================================================
# Configuration
# ==========================================================

def _find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find project root (pyproject.toml not found)")

PROJECT_ROOT = _find_project_root()
ENV_PATH = PROJECT_ROOT / ".env"
STATE_FILE = PROJECT_ROOT / "utils" / ".reauth_state"

load_dotenv(dotenv_path=ENV_PATH)

CLIENT_ID = os.getenv("TEAMLEADER_CLIENT_ID")
CLIENT_SECRET = os.getenv("TEAMLEADER_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:3000/callback"

authorization_code = None


# ==========================================================
# OAuth Callback Server
# ==========================================================

class CallbackHandler(BaseHTTPRequestHandler):
    """
    Handles OAuth redirect callback.
    Extracts authorization code from query string.
    """

    def log_message(self, format, *args):
        return  # Disable default HTTP logging

    def do_GET(self):
        global authorization_code

        query = urlparse(self.path).query
        params = parse_qs(query)

        if "code" in params:
            authorization_code = params["code"][0]
            self._send_success_response()
        else:
            self._send_error_response()

    def _send_success_response(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"""
        <html>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1 style="color: green;">Authorization successful</h1>
                <p>You may close this window.</p>
                <p>Claude will restart automatically...</p>
            </body>
        </html>
        """)

    def _send_error_response(self):
        self.send_response(400)
        self.end_headers()
        self.wfile.write(b"<html><body><h1>Authorization failed</h1></body></html>")


def start_callback_server():
    """
    Starts temporary local HTTP server to capture OAuth callback.
    Waits for a single request.
    """
    server = HTTPServer(("localhost", 3000), CallbackHandler)
    server.handle_request()


# ==========================================================
# OAuth Exchange
# ==========================================================

def exchange_code_for_tokens(code: str) -> dict:
    """
    Exchanges authorization code for access and refresh tokens.

    Args:
        code (str): OAuth authorization code

    Returns:
        dict: Token payload
    """

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
    }

    response = requests.post(
        "https://app.teamleader.eu/oauth2/access_token",
        data=payload
    )

    response.raise_for_status()
    return response.json()


# ==========================================================
# Claude Restart
# ==========================================================

def restart_claude():
    """
    Terminates and restarts Claude Desktop.
    Supports Windows and macOS.
    """

    if sys.platform == "win32":
        possible_paths = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "AnthropicClaude" / "claude.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Claude" / "Claude.exe",
            Path("C:/Users") / os.environ.get("USERNAME", "") / "AppData/Local/Programs/Claude/Claude.exe",
        ]

        claude_path = next((p for p in possible_paths if p.exists()), None)

        if not claude_path:
            raise FileNotFoundError("Claude.exe not found.")

        subprocess.run(
            ["taskkill", "/F", "/IM", "Claude.exe"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        time.sleep(2)

        subprocess.Popen(
            [str(claude_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        
    elif sys.platform == "darwin":
        possible_paths = [
            Path("/Applications/Claude.app"),
            Path.home() / "Applications" / "Claude.app",
        ]

        claude_path = next((p for p in possible_paths if p.exists()), None)

        if not claude_path:
            raise FileNotFoundError("Claude.app not found.")

        subprocess.run(
            ["pkill", "-x", "Claude"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        time.sleep(2)

        subprocess.Popen(
            ["open", str(claude_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    else:
        raise RuntimeError(f"Automatic Claude restart not supported on platform: {sys.platform}.")


# ==========================================================
# Main Reauthorization Flow
# ==========================================================

def reauthorize():
    """
    Full OAuth reauthorization lifecycle.

    Steps:
    1. Start callback server
    2. Open browser to authorize
    3. Wait for callback
    4. Exchange code for tokens
    5. Persist tokens in .env
    """

    global authorization_code

    auth_url = (
        "https://app.teamleader.eu/oauth2/authorize?"
        f"client_id={CLIENT_ID}&"
        "response_type=code&"
        f"redirect_uri={REDIRECT_URI}"
    )

    server_thread = threading.Thread(
        target=start_callback_server,
        daemon=True
    )
    server_thread.start()

    webbrowser.open(auth_url)

    server_thread.join(timeout=120)

    if not authorization_code:
        raise TimeoutError("OAuth callback not received.")

    tokens = exchange_code_for_tokens(authorization_code)

    set_key(str(ENV_PATH), "TEAMLEADER_REFRESH_TOKEN", tokens["refresh_token"])
    set_key(str(ENV_PATH), "TEAMLEADER_ACCESS_TOKEN", tokens["access_token"])

    refresh_expires_at = (
        datetime.now(timezone.utc) + timedelta(days=60)
    ).isoformat()

    access_expires_at = (
        datetime.now(timezone.utc) + timedelta(seconds=tokens.get("expires_in", 3600))
    ).isoformat()

    set_key(str(ENV_PATH), "TEAMLEADER_REFRESH_EXPIRES_AT", refresh_expires_at)
    set_key(str(ENV_PATH), "TEAMLEADER_ACCESS_EXPIRES_AT", access_expires_at)


# ==========================================================
# Entry Point
# ==========================================================

if __name__ == "__main__":

    try:
        reauthorize()

        # Signal MCP that reauthentication completed
        STATE_FILE.write_text("DONE_WAITING_RESTART")

        time.sleep(2)
        restart_claude()

        sys.exit(0)

    except Exception as e:
        print(f"Fatal error during reauthentication: {e}")
        sys.exit(1)
