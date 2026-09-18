"""
This file is the one place in the app that talks to the MySQL database.
Every other file that needs to read or write data goes through this
class instead of connecting to MySQL by itself.
"""

import re
from typing import Any, cast

import mysql.connector
from mysql.connector import Error as MySQLError
from config.settings import DB_CONFIG
from utils.exceptions import DatabaseConnectionError

#     Small wrapper around a MySQL connection.

#    Use it like this:

#        with DBConnector() as db:
#            db.execute("SELECT * FROM appointments")
#            rows = db.fetchall()

#    If include_database is False, it connects to the MySQL server only,
#    without picking a specific database. This is used the very first
#    time, before the appointmed_db database even exists yet.

# Statements that change data and so have to be committed. Anything else
# (SELECT, SHOW, USE) needs no commit, and DDL like CREATE TABLE commits
# itself in MySQL.
WRITE_KEYWORDS = ("insert", "update", "delete", "replace")

# Leading SQL comments: "-- like this", "# like this", or /* like this */.
_LEADING_COMMENT = re.compile(r"\A\s*(?:--[^\n]*(?:\n|\Z)|\#[^\n]*(?:\n|\Z)|/\*.*?\*/)")


def _first_keyword(query):
    """The first real SQL word of `query`, lowercased, ignoring any
    comments in front of it.

    Checking query.strip().startswith("insert") directly looks like it
    works and quietly doesn't: a statement read out of a .sql file
    usually arrives with its explanatory comment still attached, so it
    starts with "--", the commit is skipped, and the write is rolled
    back when the connection closes. That is exactly how the default
    admin account went missing on a fresh install."""
    text = query
    while True:
        match = _LEADING_COMMENT.match(text)
        if match is None:
            break
        text = text[match.end():]

    words = text.strip().split(None, 1)
    if not words:
        return ""
    return words[0].lower()


class DBConnector:
    def __init__(self, include_database=True):
        self.include_database = include_database
        self.connection: Any = None
        self.cursor: Any = None

    def connect(self):
        try:
            config = dict(DB_CONFIG)
            if self.include_database is False:
                config.pop("database", None)
            self.connection = mysql.connector.connect(**config)
            self.cursor = self.connection.cursor(dictionary=True)
        except MySQLError as e:
            raise DatabaseConnectionError("Could not connect to database: " + str(e))

    def _ensure_connected(self):
        if self.connection is None or self.cursor is None:
            raise DatabaseConnectionError("Database connection is not available.")

    @property
    def lastrowid(self):
        self._ensure_connected()
        return self.cursor.lastrowid

    @property
    def rowcount(self):
        self._ensure_connected()
        return self.cursor.rowcount

    def commit(self):
        """Save whatever this connection has written so far. execute()
        already does this for single write statements; call it directly
        when several writes need to land together (see the initializer)."""
        self._ensure_connected()
        self.connection.commit()

    def execute(self, query, params=()):
        self._ensure_connected()
        try:
            self.cursor.execute(query, params)
            if _first_keyword(query) in WRITE_KEYWORDS:
                self.connection.commit()
        except MySQLError as e:
            raise DatabaseConnectionError("Query failed: " + str(e))

    def fetchall(self):
        self._ensure_connected()
        return cast(list[dict[str, Any]], self.cursor.fetchall())

    def fetchone(self):
        self._ensure_connected()
        row = self.cursor.fetchone()
        if row is None:
            return None
        return cast(dict[str, Any], row)

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
