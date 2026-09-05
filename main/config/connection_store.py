"""
Remembers the last-used database host + username across app restarts,
so returning users don't have to retype the server address every time.

The password is deliberately NEVER saved here — only host and username
persist to disk. This is plain JSON, not encrypted, so it's meant for
convenience (not secrets) — good enough for a class project, but worth
noting as a limitation in real deployments.
"""

import json
import os

STORE_PATH = os.path.join(os.path.dirname(__file__), "remembered_connection.json")


def load_remembered() -> dict | None:
    """Returns {"host": ..., "user": ...} if a connection was saved before,
    or None if nothing has been remembered yet (or the file is unreadable)."""
    if not os.path.exists(STORE_PATH):
        return None
    try:
        with open(STORE_PATH, "r") as f:
            data = json.load(f)
        if "host" in data and "user" in data:
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def save_remembered(host: str, user: str):
    """Saves the host + username so next launch can pre-fill them.
    Never call this with a password — only host/user are meant to persist."""
    try:
        with open(STORE_PATH, "w") as f:
            json.dump({"host": host, "user": user}, f)
    except OSError:
        pass  # non-fatal — worst case, the user just has to retype it next time
