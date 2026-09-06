"""
Automatically applies database/schema.sql the first time the app
connects, so no one needs to open MySQL Workbench manually.

How the connection actually works, step by step:
  1. MySQL SERVER must already be running (installed once, via the
     normal MySQL installer, running as a background Windows Service).
     That install step is unavoidable — some database engine has to be
     listening on the network for other devices to reach.
  2. This module connects to that SERVER using config/settings.py's
     host/port/user/password — WITHOUT selecting a specific database,
     since appointmed_db may not exist yet.
  3. It runs schema.sql over that connection, which starts with
     `CREATE DATABASE IF NOT EXISTS appointmed_db;` — so the app
     creates its own database, tables, and default admin account.
  4. Every connection after that (via the normal DBConnector) selects
     appointmed_db as usual, since step 3 just created it.

Call ensure_database_ready() once, early in main.py, before opening
the login window.
"""

import os
from database.db_connector import DBConnector
from utils.exceptions import DatabaseConnectionError

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def ensure_database_ready():
    """Connects to the MySQL server and applies schema.sql if the
    database/tables don't already exist. Safe to call every launch —
    the schema uses CREATE ... IF NOT EXISTS throughout, so re-running
    it against an already-set-up database is a harmless no-op."""

    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(f"schema.sql not found at {SCHEMA_PATH}")

    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()

    # Split on semicolons to run statements one at a time — the
    # mysql-connector library doesn't support multi-statement execute()
    # by default in this simple setup.
    statements = [s.strip() for s in schema_sql.split(";") if s.strip()]

    try:
        with DBConnector(include_database=False) as db:
            for statement in statements:
                db.execute(statement)
    except DatabaseConnectionError as e:
        raise DatabaseConnectionError(
            f"Could not set up the database automatically. Make sure MySQL "
            f"Server is installed and running, and that config/settings.py "
            f"has the correct host/user/password. Original error: {e}"
        )
