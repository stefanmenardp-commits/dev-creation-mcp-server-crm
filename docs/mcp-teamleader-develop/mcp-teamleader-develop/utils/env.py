"""
Environment Utilities Module

This module centralizes access to the `.env` file.
It provides safe helpers to:

- Load environment variables
- Retrieve variables
- Persist updated variables (e.g. tokens)
- Ensure consistency after writes

Important:
This module should remain generic and reusable across connectors.
It must not contain any business or OAuth logic.
"""

import os
from pathlib import Path
from dotenv import load_dotenv, set_key

# Root directory of the project — anchored on pyproject.toml
def _find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find project root (pyproject.toml not found)")

PROJECT_ROOT = _find_project_root()

# Central .env file
ENV_PATH = PROJECT_ROOT / ".env"


def reload_env() -> None:
    """
    Reloads environment variables from the .env file.

    This must be called after writing tokens to ensure
    the current process reflects updated values.
    """
    load_dotenv(dotenv_path=ENV_PATH, override=True)


def get_env(key: str) -> str | None:
    """
    Retrieves an environment variable from the .env file.

    Args:
        key (str): Environment variable name

    Returns:
        str | None: Value if exists, otherwise None
    """
    reload_env()
    return os.getenv(key)


def set_env(key: str, value: str) -> None:
    """
    Persists a variable into the .env file and reloads it.

    Args:
        key (str): Variable name
        value (str): Value to store
    """
    set_key(str(ENV_PATH), key, value)
    reload_env()


if __name__ == "__main__":

    try:
        print(get_env("TEAMLEADER_REFRESH_TOKEN"))


    except Exception as e:
        print(f"Fatal error during reauthentication: {e}")