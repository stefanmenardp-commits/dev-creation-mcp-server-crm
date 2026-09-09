"""
Teamleader OAuth Authentication Module

This module is responsible for:
- Ensuring a valid access token is always returned
- Refreshing expired access tokens
- Triggering full reauthentication when needed
- Managing restart lifecycle of the MCP process
"""

import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import requests

from utils.env import get_env, set_env, reload_env, PROJECT_ROOT
from utils.state import get_reauth_state, set_reauth_state


# ==========================================================
# Public function used by API layer
# ==========================================================

def get_valid_access_token() -> str:
    """
    Ensures a valid access token is available.

    Handles:
    - Missing refresh token → full reauthentication
    - Refresh token expiring soon → full reauthentication
    - Expired access token → silent refresh
    - Restart after reauth → state reset

    Returns:
        str: A valid access token
    """

    just_reauthed = False

    state = get_reauth_state()

    # If we just restarted after reauthentication,
    # consume the state and reset it.
    if state == "IN_PROGRESS":
        set_reauth_state("NONE")
        reload_env()

    # If we just restarted after reauthentication,
    # consume the state and reset it.
    if state == "DONE_WAITING_RESTART":
        set_reauth_state("NONE")
        reload_env()
        just_reauthed = True

    reload_env()

    refresh_token = get_env("TEAMLEADER_REFRESH_TOKEN")
    refresh_expires_at = get_env("TEAMLEADER_REFRESH_EXPIRES_AT")
    access_expires_at = get_env("TEAMLEADER_ACCESS_EXPIRES_AT")

    now = datetime.now(timezone.utc)
    need_reauth = False

    # 1️⃣ No refresh token available → must reauthenticate
    if not refresh_token:
        need_reauth = True

    # 2️⃣ Refresh token expiring soon → proactive reauthentication
    elif refresh_expires_at and not just_reauthed:
        expiry = datetime.fromisoformat(refresh_expires_at.replace("Z", "+00:00"))
        if expiry - now < timedelta(days=7):
            need_reauth = True

    if need_reauth:
        launch_reauthentication()

    # 3️⃣ Access token expired → silent refresh
    if access_expires_at:
        access_expiry = datetime.fromisoformat(access_expires_at.replace("Z", "+00:00"))
        if access_expiry <= now:
            return refresh_access_token()

    access_token = get_env("TEAMLEADER_ACCESS_TOKEN")

    # 4️⃣ No access token stored → refresh it
    if not access_token:
        return refresh_access_token()

    return access_token


# ==========================================================
# Internal helpers
# ==========================================================

def refresh_access_token() -> str:
    """
    Refreshes the access token using the refresh token.

    Returns:
        str: New access token
    """

    refresh_token = get_env("TEAMLEADER_REFRESH_TOKEN")
    client_id = get_env("TEAMLEADER_CLIENT_ID")
    client_secret = get_env("TEAMLEADER_CLIENT_SECRET")

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    response = requests.post(
        "https://app.teamleader.eu/oauth2/access_token",
        data=payload
    )

    response.raise_for_status()
    data = response.json()

    access_token = data["access_token"]
    expires_in = data.get("expires_in", 3600)

    set_env("TEAMLEADER_ACCESS_TOKEN", access_token)

    access_expires_at = (
        datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    ).isoformat()

    set_env("TEAMLEADER_ACCESS_EXPIRES_AT", access_expires_at)

    if "refresh_token" in data:
        set_env("TEAMLEADER_REFRESH_TOKEN", data["refresh_token"])

    return access_token


def launch_reauthentication():
    """
    Launches the external reauthentication script and
    immediately terminates the current MCP process.

    This ensures:
    - No duplicate authentication
    - Clean lifecycle restart
    """

    if get_reauth_state() == "IN_PROGRESS":
        os._exit(0)

    set_reauth_state("IN_PROGRESS")

    script_path = PROJECT_ROOT / "scripts" / "auto_reauth.py"
    print(script_path)

    subprocess.Popen([sys.executable, str(script_path)], cwd=str(PROJECT_ROOT))

    # Immediately terminate MCP process
    os._exit(0)