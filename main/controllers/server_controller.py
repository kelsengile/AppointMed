"""
Business logic for the Server page: checking that the shared MySQL
database is reachable and (for admins) pointing the app at a different
server.

Nothing here draws anything - the view (views/shared/server_page.py) just
calls these methods and shows the results.

Note: the password is only ever kept in memory (settings.DB_CONFIG). Like
config/connection_store.py, only the host and username are written to disk.
"""

import time

from config import settings
from config.connection_store import save_remembered
from database.db_connector import DBConnector
from utils.exceptions import DatabaseConnectionError, EmptyFieldError, InvalidInputError


class ServerController:

    TIMEOUT_SECONDS = 5     # don't let an unreachable server freeze the app
    # (table name, label shown on the Server page) - fixed list, never user input
    STAT_TABLES = (("users", "Users"), ("appointments", "Appointments"), ("invoices", "Invoices"))

    def current_settings(self):
        """The connection settings the app is using right now."""
        cfg = settings.DB_CONFIG
        return {
            "host": cfg.get("host", ""),
            "port": cfg.get("port", 3306),
            "user": cfg.get("user", ""),
            "database": cfg.get("database", ""),
        }

    def check_connection(self, overrides=None):
        """Tries to connect and returns a dictionary. It never raises, so
        it is safe to run on a background thread.

            {"ok": True,  "latency_ms": 12, "version": "8.0.36",
             "counts": {"Users": 4, "Appointments": 20, "Invoices": 3}}
            {"ok": False, "error": "Could not connect to database: ..."}

        `overrides` (host/port/user/password) lets the page test values
        typed in the form before they are saved; anything left out falls
        back to the current settings."""
        config = dict(settings.DB_CONFIG)
        if overrides:
            config.update(overrides)
        config["connection_timeout"] = self.TIMEOUT_SECONDS

        started = time.perf_counter()
        try:
            with DBConnector(config=config) as db:
                latency_ms = round((time.perf_counter() - started) * 1000)
                db.execute("SELECT VERSION() AS version")
                version = db.fetchone()["version"]
                counts = {}
                for table, label in self.STAT_TABLES:
                    try:
                        db.execute("SELECT COUNT(*) AS total FROM " + table)
                        counts[label] = db.fetchone()["total"]
                    except DatabaseConnectionError:
                        counts[label] = None    # table missing on this server
        except Exception as e:
            return {"ok": False, "error": str(e)}

        return {"ok": True, "latency_ms": latency_ms, "version": version, "counts": counts}

    def apply_settings(self, host, port, user, password=""):
        """Validates, TESTS, and only then switches the app to the new
        server (so a typo can't leave it pointed at a dead address).
        Remembers host + username for next launch. A blank password keeps
        the current one. Raises an AppointMedError on any problem."""
        host = (host or "").strip()
        user = (user or "").strip()
        if not host:
            raise EmptyFieldError("Server host is required.")
        if not user:
            raise EmptyFieldError("Database user is required.")
        try:
            port = int(str(port).strip())
        except ValueError:
            raise InvalidInputError("Port must be a number, like 3306.")
        if not 1 <= port <= 65535:
            raise InvalidInputError("Port must be between 1 and 65535.")

        candidate = {"host": host, "port": port, "user": user}
        if password:
            candidate["password"] = password

        result = self.check_connection(candidate)
        if not result["ok"]:
            raise DatabaseConnectionError(result["error"])

        settings.DB_CONFIG.update(candidate)
        save_remembered(host, user)
        return result