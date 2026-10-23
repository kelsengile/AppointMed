"""MySQL access.

Repositories only depend on the small `Executor` interface. Two implementations exist:
  * Database     - every call runs on its own pooled connection and is committed at once.
  * Transaction  - several calls share one connection and commit or roll back together.
SQL is always parameterized: values are passed separately from the query text.
"""

from __future__ import annotations

import logging
import threading
from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator, Sequence

from mysql.connector import errorcode, pooling
from mysql.connector.errors import Error as MySQLError
from mysql.connector.errors import IntegrityError

from .config import settings
from .exceptions import ConflictError, DatabaseUnavailableError, DuplicateEntryError

logger = logging.getLogger("appointmed")

Row = dict[str, Any]
Params = Sequence[Any]


def _translate(exc: MySQLError) -> Exception:
    """Map a driver error to one of our own errors (never leaks SQL details to users)."""
    if isinstance(exc, IntegrityError):
        if exc.errno == errorcode.ER_DUP_ENTRY:
            return DuplicateEntryError()
        return ConflictError("The change conflicts with existing records.")
    logger.error("Database error: %s", exc)
    return DatabaseUnavailableError()


def _run(cursor: Any, sql: str, params: Params) -> None:
    """Execute one statement, translating driver errors."""
    try:
        cursor.execute(sql, tuple(params))
    except MySQLError as exc:
        raise _translate(exc) from exc


class Executor(ABC):
    """Abstract way to run SQL. Repositories depend on this, not on a concrete connection."""

    @abstractmethod
    def fetch_all(self, sql: str, params: Params = ()) -> list[Row]:
        """Run a SELECT and return all rows as dictionaries."""

    @abstractmethod
    def execute(self, sql: str, params: Params = ()) -> int:
        """Run an INSERT and return the new row id."""

    @abstractmethod
    def update(self, sql: str, params: Params = ()) -> int:
        """Run an UPDATE or DELETE and return the number of rows changed."""

    def fetch_one(self, sql: str, params: Params = ()) -> Row | None:
        """Run a SELECT and return the first row, or None."""
        rows = self.fetch_all(sql, params)
        return rows[0] if rows else None

    def server_now(self) -> datetime:
        """The database clock, so 'now' agrees with CURDATE()/NOW() used in queries."""
        row = self.fetch_one("SELECT NOW() AS current_time_value")
        return row["current_time_value"] if row else datetime.now()


class Transaction(Executor):
    """Several statements on one connection. Commit/rollback is handled by Database.transaction()."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def fetch_all(self, sql: str, params: Params = ()) -> list[Row]:
        cursor = self._connection.cursor(dictionary=True)
        try:
            _run(cursor, sql, params)
            return cursor.fetchall()
        finally:
            cursor.close()

    def execute(self, sql: str, params: Params = ()) -> int:
        cursor = self._connection.cursor(dictionary=True)
        try:
            _run(cursor, sql, params)
            return int(cursor.lastrowid or 0)
        finally:
            cursor.close()

    def update(self, sql: str, params: Params = ()) -> int:
        cursor = self._connection.cursor(dictionary=True)
        try:
            _run(cursor, sql, params)
            return int(cursor.rowcount)
        finally:
            cursor.close()


class Database(Executor):
    """Connection pool wrapper. The pool is created on first use so the app starts even if MySQL is down."""

    def __init__(self) -> None:
        self._pool: pooling.MySQLConnectionPool | None = None
        self._lock = threading.Lock()

    def _get_pool(self) -> pooling.MySQLConnectionPool:
        with self._lock:
            if self._pool is None:
                try:
                    self._pool = pooling.MySQLConnectionPool(
                        pool_name="appointmed",
                        pool_size=8,
                        pool_reset_session=True,
                        host=settings.db_host,
                        port=settings.db_port,
                        database=settings.db_name,
                        user=settings.db_user,
                        password=settings.db_password,
                        charset="utf8mb4",
                        autocommit=True,
                        connection_timeout=5,
                    )
                except MySQLError as exc:
                    logger.error("Could not create the connection pool: %s", exc)
                    raise DatabaseUnavailableError() from exc
            return self._pool

    @contextmanager
    def connection(self) -> Iterator[Any]:
        """Borrow a pooled connection and always give it back."""
        try:
            conn = self._get_pool().get_connection()
        except MySQLError as exc:
            logger.error("Could not get a connection: %s", exc)
            raise DatabaseUnavailableError() from exc
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Iterator[Transaction]:
        """All statements inside the `with` block succeed together or are rolled back."""
        with self.connection() as conn:
            tx = Transaction(conn)
            conn.start_transaction()
            try:
                yield tx
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    def fetch_all(self, sql: str, params: Params = ()) -> list[Row]:
        with self.connection() as conn:
            return Transaction(conn).fetch_all(sql, params)

    def execute(self, sql: str, params: Params = ()) -> int:
        with self.connection() as conn:
            return Transaction(conn).execute(sql, params)

    def update(self, sql: str, params: Params = ()) -> int:
        with self.connection() as conn:
            return Transaction(conn).update(sql, params)

    def is_reachable(self) -> bool:
        """True when a trivial query succeeds. Used by the health check."""
        try:
            return self.fetch_one("SELECT 1 AS ok") is not None
        except DatabaseUnavailableError:
            return False


database = Database()