"""
Single point of contact between the app and the MySQL server.
Every device running AppointMed points this at the same host, which is
what keeps all clients in sync with one shared source of truth.
"""

import mysql.connector
from mysql.connector import Error as MySQLError
from config.settings import DB_CONFIG
from utils.exceptions import DatabaseConnectionError


class DBConnector:
    """Wraps a MySQL connection. Use as a context manager:

        with DBConnector() as db:
            db.execute("SELECT * FROM appointments")
            rows = db.fetchall()

    Pass include_database=False to connect to the SERVER only, without
    selecting a specific database — needed the very first time, before
    appointmed_db has even been created (see database/initializer.py).
    """

    def __init__(self, include_database: bool = True):
        self._include_database = include_database
        self._connection = None
        self._cursor = None

    def connect(self):
        try:
            config = dict(DB_CONFIG)
            if not self._include_database:
                config.pop("database", None)
            self._connection = mysql.connector.connect(**config)
            self._cursor = self._connection.cursor(dictionary=True)
        except MySQLError as e:
            raise DatabaseConnectionError(f"Could not connect to database: {e}")

    def execute(self, query: str, params: tuple = ()):
        try:
            self._cursor.execute(query, params)
            if query.strip().lower().startswith(("insert", "update", "delete")):
                self._connection.commit()
        except MySQLError as e:
            raise DatabaseConnectionError(f"Query failed: {e}")

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchone(self):
        return self._cursor.fetchone()

    def close(self):
        if self._cursor:
            self._cursor.close()
        if self._connection:
            self._connection.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
