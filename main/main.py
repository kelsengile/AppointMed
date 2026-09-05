"""
AppointMed — entry point.
Run this file on every client device; each one connects to the same
central database (see config/settings.py) so all users stay in sync.

The app is usable even with NO database connection: it always opens
the login window. If a database is reachable, it's set up automatically
(tables + default admin created if missing). If not, the login screen
still opens — the user can use "Connect to Server" to point the app at
a database, or just see a clear "can't reach the server" message when
they try to log in.
"""

from config import settings
from config.connection_store import load_remembered
from database.initializer import ensure_database_ready

if __name__ == "__main__":
    # Apply a remembered host/username (if any) before the first connection
    # attempt, so a returning user's server address is used automatically.
    remembered = load_remembered()
    if remembered:
        settings.DB_CONFIG["host"] = remembered["host"]
        settings.DB_CONFIG["user"] = remembered["user"]

    # Best-effort auto-setup. Failure here is expected and fine if no
    # database is reachable yet — the login window still opens either way.
    try:
        ensure_database_ready()
    except Exception:
        pass

    from views.shared.login_view import LoginView
    app = LoginView()
    app.mainloop()