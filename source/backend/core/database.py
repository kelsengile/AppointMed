"""MySQL access. A Session is one connection and one transaction."""

from contextlib import contextmanager
from typing import Any, Iterator, Sequence

import mysql.connector
from mysql.connector import Error as MySQLError

from backend.core.config import Settings, settings
from backend.core.exceptions import ServiceUnavailableError


class Session:
    """One open connection. Repositories receive it and run their SQL through it."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def all(self, sql: str, params: Sequence[Any] = ()) -> list[dict]:
        """Run a SELECT and return every row as a dict."""
        cursor = self._connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, params)
            return cursor.fetchall()
        finally:
            cursor.close()

    def one(self, sql: str, params: Sequence[Any] = ()) -> dict | None:
        """Run a SELECT and return the first row, or None."""
        rows = self.all(sql, params)
        return rows[0] if rows else None

    def execute(self, sql: str, params: Sequence[Any] = ()) -> int:
        """Run an INSERT/UPDATE/DELETE and return the new row id (if any)."""
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql, params)
            return cursor.lastrowid or 0
        finally:
            cursor.close()


class Database:
    """Creates connections and transactions for the backend."""

    def __init__(self, config: Settings) -> None:
        self._config = config

    def connect(self):
        return mysql.connector.connect(
            host=self._config.db_host,
            port=self._config.db_port,
            database=self._config.db_name,
            user=self._config.db_user,
            password=self._config.db_password,
            connection_timeout=3,
        )

    def is_reachable(self) -> bool:
        """True if the app can connect and run a trivial query."""
        try:
            connection = self.connect()
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
            finally:
                connection.close()
            return True
        except MySQLError:
            return False

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Open a transaction: commit if the block succeeds, roll back if it raises."""
        try:
            connection = self.connect()
        except MySQLError as exc:
            raise ServiceUnavailableError("The database is unavailable right now. Please try again shortly.") from exc
        try:
            yield Session(connection)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


database = Database(settings)