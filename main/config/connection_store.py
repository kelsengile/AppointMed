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


def load_remembered():
    """Returns a dictionary like {"host": ..., "user": ...} if we saved a
    connection before. Returns None if nothing was saved yet or the file
    could not be read."""
    if not os.path.exists(STORE_PATH):
        return None

    try:
        file = open(STORE_PATH, "r")
        data = json.load(file)
        file.close()
    except (json.JSONDecodeError, OSError):
        return None

    if "host" in data and "user" in data:
        return data
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
