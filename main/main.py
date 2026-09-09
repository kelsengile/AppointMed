"""
AppointMed — entry point.
Run this file on every device. Every device connects to the same
central database (see config/settings.py) so all users stay in sync.

The app still opens even if there is no database connection yet: it
always shows the login window. If a database IS reachable, it gets set
up automatically (tables and the default admin account are created if
they are missing). If not, the login screen still opens - the user can
click "Connect to Server" to point the app at a database, or they will
just see a clear error message when they try to log in.
"""

from config import settings
from config.connection_store import load_remembered
from database.initializer import ensure_database_ready

if __name__ == "__main__":
    # If we remembered a host/username from before, use it now, so a
    # returning user does not have to type the server address again.
    remembered = load_remembered()
    if remembered:
        settings.DB_CONFIG["host"] = remembered["host"]
        settings.DB_CONFIG["user"] = remembered["user"]

    # Try to set up the database automatically. If this fails (for
    # example, no database is reachable yet), that is fine - the login
    # window still opens either way.
    try:
        ensure_database_ready()
    except Exception:
        pass

    from views.shared.login_view import LoginView
    app = LoginView()
    app.mainloop()
