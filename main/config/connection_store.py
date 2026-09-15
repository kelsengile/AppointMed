"""
Remembers the last-used database host and username so the user does not
have to type the server address every time they open the app.

We never save the password here, only the host and username. This is
just a plain text file (JSON), so it is not secure - it is only meant
to save the user some typing, which is fine for a class project.
"""

import json
import os

STORE_PATH = os.path.join(os.path.dirname(__file__), "remembered_connection.json")


def load_remembered() -> dict[str, str] | None:
    """Returns a dictionary like {"host": ..., "user": ...} if we saved a
    connection before. Returns None if nothing was saved yet or the file
    could not be read."""
    if not os.path.exists(STORE_PATH):
        return None

    try:
        with open(STORE_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return None

    if not isinstance(data, dict):
        return None

    host = data.get("host")
    user = data.get("user")
    if isinstance(host, str) and isinstance(user, str) and host and user:
        return {"host": host, "user": user}
    return None


def save_remembered(host, user):
    """Saves the host and username to a file so next time the app opens,
    it can fill them in automatically. Never pass a password in here."""
    try:
        file = open(STORE_PATH, "w")
        json.dump({"host": host, "user": user}, file)
        file.close()
    except OSError:
        # Not a big deal if this fails - the user just types it again.
        pass
