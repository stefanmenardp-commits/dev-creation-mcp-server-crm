"""
Process State Management Module

This module handles lifecycle coordination between:

- MCP process
- Reauthentication script
- Claude restart cycle

The state file acts as a lightweight inter-process flag system.

States:
- NONE
- IN_PROGRESS
- DONE_WAITING_RESTART
"""

from utils.env import PROJECT_ROOT


STATE_FILE = PROJECT_ROOT / "utils" / ".reauth_state"


def get_reauth_state() -> str:
    """
    Returns the current reauthentication state.

    Returns:
        str: Current state (default = "NONE")
    """
    if not STATE_FILE.exists():
        return "NONE"

    return STATE_FILE.read_text().strip()


def set_reauth_state(state: str) -> None:
    """
    Updates the reauthentication state.

    Args:
        state (str): New lifecycle state
    """
    STATE_FILE.write_text(state)
