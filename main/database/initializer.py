"""
This file sets up the database automatically the first time the app
connects, by running database/schema.sql. This means nobody has to open
MySQL Workbench by hand just to create the tables.

How it works, step by step:
  1. MySQL Server must already be installed and running on some
     computer that every device can reach over the network.
  2. This file connects to that server using the host/port/user/password
     from config/settings.py, but WITHOUT picking a database yet,
     since appointmed_db might not exist.
  3. It runs schema.sql, which starts with
     "CREATE DATABASE IF NOT EXISTS appointmed_db;" so the app creates
     its own database, tables, and a default admin account.
  4. After that, every normal connection (through DBConnector) picks
     appointmed_db like usual, since step 3 already created it.

Call ensure_database_ready() once near the start of main.py, before the
login window opens.
"""

import os
from database.db_connector import DBConnector
from utils.exceptions import DatabaseConnectionError

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def ensure_database_ready():
    """Connects to the MySQL server and runs schema.sql if the database
    or tables are not there yet. It is safe to call this every time the
    app starts, because the schema uses "IF NOT EXISTS" everywhere, so
    running it again on an already set up database just does nothing."""

    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError("schema.sql not found at " + SCHEMA_PATH)

    schema_file = open(SCHEMA_PATH, "r")
    schema_sql = schema_file.read()
    schema_file.close()

    # Break the file into separate statements, since the mysql-connector
    # library we're using can only run one SQL statement at a time.
    raw_statements = schema_sql.split(";")
    statements = []
    for statement in raw_statements:
        statement = statement.strip()
        if statement != "":
            statements.append(statement)

    try:
        with DBConnector(include_database=False) as db:
            for statement in statements:
                db.execute(statement)
    except DatabaseConnectionError as e:
        raise DatabaseConnectionError(
            "Could not set up the database automatically. Make sure MySQL "
            "Server is installed and running, and that config/settings.py "
            "has the correct host/user/password. Original error: " + str(e)
        )
