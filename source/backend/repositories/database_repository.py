"""SQL for the admin Database page: table metadata, generic row access, and the SQL backup dump.

Unlike the other repositories this one works with any table, so table names are always checked
against the list in information_schema before being used, and every value is still parameterized.
`admin_session` gives one connection whose driver errors are turned into messages an administrator
can read (for example "Cannot delete a parent row"), instead of the generic 503 used elsewhere.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any, Iterator

from mysql.connector.errors import Error as MySQLError
from mysql.connector.errors import IntegrityError, InterfaceError, OperationalError

from backend.core.config import settings
from backend.core.database import Database, Executor, Params, Row
from backend.core.exceptions import ConflictError, DatabaseUnavailableError, ValidationFailedError

logger = logging.getLogger("appointmed")

# Dump order: parents before children (foreign key checks are also switched off while loading).
_TABLE_ORDER = (
    "users", "doctor_schedules", "rooms", "notifications", "patients", "appointments", "examinations",
    "prescriptions", "prescription_items", "invoices", "clinic_settings", "audit_logs",
)
_ESCAPES = {"\\": "\\\\", "'": "\\'", "\0": "\\0", "\n": "\\n", "\r": "\\r", "\x1a": "\\Z"}


def _fail(exc: MySQLError) -> Exception:
    """Turn a driver error into one of our errors with a readable message."""
    message = getattr(exc, "msg", None) or str(exc)
    if isinstance(exc, (InterfaceError, OperationalError)):
        logger.error("Database error: %s", exc)
        return DatabaseUnavailableError()
    if isinstance(exc, IntegrityError):
        return ConflictError(f"MySQL refused the change: {message}")
    return ValidationFailedError(f"MySQL rejected this: {message}")


class AdminSession(Executor):
    """One connection that maps driver errors with `_fail`. Commit and rollback are done by admin_session()."""

    def __init__(self, connection: Any) -> None:
        self._conn = connection

    def fetch_all(self, sql: str, params: Params = ()) -> list[Row]:
        cursor = self._conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, tuple(params) if params else None)
            return cursor.fetchall()
        except MySQLError as exc:
            raise _fail(exc) from exc
        finally:
            cursor.close()

    def execute(self, sql: str, params: Params = ()) -> int:
        cursor = self._conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, tuple(params) if params else None)
            return int(cursor.lastrowid or 0)
        except MySQLError as exc:
            raise _fail(exc) from exc
        finally:
            cursor.close()

    def update(self, sql: str, params: Params = ()) -> int:
        cursor = self._conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, tuple(params) if params else None)
            return int(cursor.rowcount)
        except MySQLError as exc:
            raise _fail(exc) from exc
        finally:
            cursor.close()

    def select(self, sql: str) -> tuple[list[str], list[tuple]]:
        """Run a SELECT typed by the administrator. Returns the column names and the rows."""
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql)
            names = [str(item[0]) for item in (cursor.description or [])]
            rows = cursor.fetchall() if cursor.description else []
            return names, rows
        except MySQLError as exc:
            raise _fail(exc) from exc
        finally:
            cursor.close()


@contextmanager
def admin_session(db: Database) -> Iterator[AdminSession]:
    """Everything inside the `with` block commits together, or rolls back on any error."""
    with db.connection() as conn:
        session = AdminSession(conn)
        try:
            conn.start_transaction()
        except MySQLError as exc:
            raise _fail(exc) from exc
        try:
            yield session
            conn.commit()
        except BaseException:
            conn.rollback()
            raise


def _s(value: Any) -> str:
    """information_schema text sometimes arrives as bytes."""
    if value is None:
        return ""
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", "replace")
    return str(value)


def quote(name: str) -> str:
    """Backtick-quote an identifier that was already validated against information_schema."""
    return "`" + name.replace("`", "``") + "`"


def _clock(value: timedelta) -> str:
    total = int(value.total_seconds())
    sign = "-" if total < 0 else ""
    total = abs(total)
    return f"{sign}{total // 3600:02d}:{total % 3600 // 60:02d}:{total % 60:02d}"


def to_json_value(value: Any) -> Any:
    """A value as the browser should display it (dates and money become plain text)."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, timedelta):
        return _clock(value)
    if isinstance(value, time):
        return value.strftime("%H:%M:%S")
    if isinstance(value, (bytes, bytearray)):
        return f"(binary, {len(value)} bytes)"
    return str(value)


def sql_literal(value: Any) -> str:
    """A value written as SQL text, for the backup file."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, datetime):
        return "'" + value.isoformat(sep=" ") + "'"
    if isinstance(value, date):
        return "'" + value.isoformat() + "'"
    if isinstance(value, timedelta):
        return "'" + _clock(value) + "'"
    if isinstance(value, time):
        return "'" + value.isoformat() + "'"
    if isinstance(value, (bytes, bytearray)):
        return "X'" + bytes(value).hex() + "'"
    return "'" + "".join(_ESCAPES.get(ch, ch) for ch in str(value)) + "'"


class DatabaseAdminRepository:
    """Metadata, generic row queries and the backup dump. Works on any Executor (normally an AdminSession)."""

    def __init__(self, db: Executor) -> None:
        self._db = db

    # ------------------------------------------------------------ metadata
    def table_names(self) -> list[str]:
        rows = self._db.fetch_all(
            "SELECT TABLE_NAME AS name FROM information_schema.tables "
            "WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME",
            (settings.db_name,),
        )
        return [_s(r["name"]) for r in rows]

    def columns(self, table: str) -> list[dict[str, Any]]:
        rows = self._db.fetch_all(
            "SELECT COLUMN_NAME AS name, COLUMN_TYPE AS col_type, DATA_TYPE AS data_type, IS_NULLABLE AS nullable, "
            "COLUMN_KEY AS col_key, EXTRA AS extra, GENERATION_EXPRESSION AS generation "
            "FROM information_schema.columns WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s ORDER BY ORDINAL_POSITION",
            (settings.db_name, table),
        )
        return [
            {
                "name": _s(r["name"]),
                "type": _s(r["col_type"]),
                "data_type": _s(r["data_type"]).lower(),
                "nullable": _s(r["nullable"]).upper() == "YES",
                "primary": _s(r["col_key"]) == "PRI",
                "auto": "auto_increment" in _s(r["extra"]).lower(),
                "generated": bool(_s(r["generation"]).strip()),
            }
            for r in rows
        ]

    def count(self, table: str) -> int:
        row = self._db.fetch_one(f"SELECT COUNT(*) AS n FROM {quote(table)}")
        return int(row["n"]) if row else 0

    # ------------------------------------------------------------ rows
    def page(
        self, table: str, visible: list[str], searchable: list[str], order_by: str, descending: bool,
        term: str | None, limit: int, offset: int,
    ) -> tuple[list[Row], int]:
        """A page of rows (only the `visible` columns) and the total that match the search."""
        where, params = "", []
        if term and searchable:
            where = " WHERE " + " OR ".join(f"CAST({quote(c)} AS CHAR) LIKE %s" for c in searchable)
            params = [f"%{term}%"] * len(searchable)
        total_row = self._db.fetch_one(f"SELECT COUNT(*) AS n FROM {quote(table)}{where}", params)
        rows = self._db.fetch_all(
            f"SELECT {', '.join(quote(c) for c in visible)} FROM {quote(table)}{where} "
            f"ORDER BY {quote(order_by)} {'DESC' if descending else 'ASC'} LIMIT %s OFFSET %s",
            [*params, limit, offset],
        )
        return rows, int(total_row["n"]) if total_row else 0

    def row_exists(self, table: str, key_column: str, key: str) -> bool:
        row = self._db.fetch_one(f"SELECT 1 AS hit FROM {quote(table)} WHERE {quote(key_column)} = %s LIMIT 1", (key,))
        return row is not None

    def insert(self, table: str, data: dict[str, Any]) -> int:
        """Insert one row. Returns the new auto-increment id (0 when the table has none)."""
        if not data:
            return self._db.execute(f"INSERT INTO {quote(table)} () VALUES ()")
        cols = list(data)
        return self._db.execute(
            f"INSERT INTO {quote(table)} ({', '.join(quote(c) for c in cols)}) VALUES ({', '.join(['%s'] * len(cols))})",
            [data[c] for c in cols],
        )

    def update_row(self, table: str, key_column: str, key: str, data: dict[str, Any]) -> int:
        cols = list(data)
        return self._db.update(
            f"UPDATE {quote(table)} SET {', '.join(quote(c) + ' = %s' for c in cols)} WHERE {quote(key_column)} = %s",
            [*(data[c] for c in cols), key],
        )

    def delete_row(self, table: str, key_column: str, key: str) -> int:
        return self._db.update(f"DELETE FROM {quote(table)} WHERE {quote(key_column)} = %s", (key,))

    # ------------------------------------------------------------ backup
    def dump(self) -> tuple[str, str]:
        """The whole database as SQL (structure and data). Returns the text and a one-line summary."""
        names = self.table_names()
        ordered = [n for n in _TABLE_ORDER if n in names] + [n for n in names if n not in _TABLE_ORDER]
        parts = [
            "-- AppointMed database backup",
            f"-- Database: {settings.db_name}",
            f"-- Created:  {self._db.server_now():%Y-%m-%d %H:%M:%S}",
            "--",
            "-- Restore as the MySQL root user (the app account cannot create or drop tables):",
            f"--   mysql -u root -p {settings.db_name} < this-file.sql",
            "-- Restoring REPLACES every table below. This file contains password hashes: keep it private.",
            "",
            "SET NAMES utf8mb4;",
            "SET FOREIGN_KEY_CHECKS = 0;",
            "",
        ]
        total_rows = 0
        for name in ordered:
            cols = [c for c in self.columns(name) if not c["generated"]]  # generated columns are rebuilt by MySQL
            col_names = [c["name"] for c in cols]
            key = next((c["name"] for c in cols if c["primary"]), None)
            create = self._db.fetch_one(f"SHOW CREATE TABLE {quote(name)}")
            create_sql = _s(create["Create Table"]) if create else ""
            order = f" ORDER BY {quote(key)}" if key else ""
            rows = self._db.fetch_all(f"SELECT {', '.join(quote(c) for c in col_names)} FROM {quote(name)}{order}")
            total_rows += len(rows)
            parts += [
                "-- ------------------------------------------------------------",
                f"-- Table: {name} ({len(rows)} rows)",
                "-- ------------------------------------------------------------",
                f"DROP TABLE IF EXISTS {quote(name)};",
                create_sql + ";",
                "",
            ]
            column_list = ", ".join(quote(c) for c in col_names)
            for start in range(0, len(rows), 100):
                values = ",\n".join(
                    "(" + ", ".join(sql_literal(r[c]) for c in col_names) + ")" for r in rows[start : start + 100]
                )
                parts.append(f"INSERT INTO {quote(name)} ({column_list}) VALUES\n{values};")
            parts.append("")
        parts += ["SET FOREIGN_KEY_CHECKS = 1;", ""]
        return "\n".join(parts), f"{len(ordered)} tables, {total_rows} rows"