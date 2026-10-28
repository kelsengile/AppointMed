"""Database page: browse and edit table rows, run one SQL statement, and download a backup.

Only administrators reach this (feature "database"). Every change is written to the audit log
(without the values, so no personal or medical data ends up there).
"""

from __future__ import annotations

import re
from typing import Any

from backend.core.database import Database, database
from backend.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError, ValidationFailedError
from backend.models.domain import User
from backend.repositories.database_repository import DatabaseAdminRepository, admin_session, to_json_value
from backend.repositories.system_repository import AuditRepository

_HIDDEN = frozenset({"password_hash", "avatar"})  # never shown in the browser or the console
_READ_ONLY = frozenset({"audit_logs"})  # the audit log is append-only
_NO_INSERT = frozenset({"users"})  # new accounts need a hashed password: use the Users page
_TEXT_TYPES = frozenset({"char", "varchar", "tinytext", "text", "mediumtext", "longtext"})
_READ_KINDS = frozenset({"select", "show", "describe", "desc", "explain"})
_CONSOLE_LIMIT = 500


class DatabaseService:
    """Rules for the administrator's database tools."""

    def __init__(self, db: Database = database) -> None:
        self._db = db

    # ------------------------------------------------------------ helpers
    @staticmethod
    def _describe(repo: DatabaseAdminRepository, name: str) -> dict[str, Any]:
        """Column details and the rules for one table. The name must be a real table."""
        if name not in repo.table_names():
            raise NotFoundError("Table not found.")
        columns = repo.columns(name)
        for column in columns:
            column["hidden"] = column["name"] in _HIDDEN
        keys = [c["name"] for c in columns if c["primary"]]
        primary = keys[0] if len(keys) == 1 else None
        read_only = name in _READ_ONLY or primary is None
        return {
            "name": name,
            "columns": columns,
            "primary_key": primary,
            "read_only": read_only,
            "can_insert": not read_only and name not in _NO_INSERT,
        }

    @staticmethod
    def _clean(meta: dict[str, Any], values: dict[str, Any], inserting: bool) -> dict[str, Any]:
        """Check the column names and turn blanks into defaults (insert) or NULL (edit)."""
        known = {c["name"]: c for c in meta["columns"]}
        cleaned: dict[str, Any] = {}
        for key, raw in values.items():
            column = known.get(key)
            if column is None or column["generated"] or column["hidden"]:
                raise ValidationFailedError(f"The column '{key}' cannot be set here.")
            if not inserting and column["primary"]:
                raise ValidationFailedError("The primary key cannot be changed.")
            value = raw.strip() if isinstance(raw, str) else raw
            if isinstance(value, bool):
                value = int(value)
            if value is None or value == "":
                if inserting:
                    continue  # blank on insert means "let MySQL use the default"
                if column["nullable"]:
                    value = None
                elif column["data_type"] in _TEXT_TYPES:
                    value = ""
                else:
                    raise ValidationFailedError(f"The column '{key}' cannot be empty.")
            cleaned[key] = value
        return cleaned

    @staticmethod
    def _writable(meta: dict[str, Any]) -> None:
        if meta["read_only"]:
            raise ConflictError("This table cannot be changed here (the audit log is append-only).")

    # ------------------------------------------------------------ browsing
    def tables(self) -> list[dict[str, Any]]:
        with admin_session(self._db) as session:
            repo = DatabaseAdminRepository(session)
            result = []
            for name in repo.table_names():
                meta = self._describe(repo, name)
                result.append(
                    {
                        "name": name,
                        "rows": repo.count(name),
                        "columns": len(meta["columns"]),
                        "read_only": meta["read_only"],
                        "can_insert": meta["can_insert"],
                    }
                )
            return result

    def table(self, name: str, term: str | None, limit: int, offset: int) -> dict[str, Any]:
        with admin_session(self._db) as session:
            repo = DatabaseAdminRepository(session)
            meta = self._describe(repo, name)
            columns = meta["columns"]
            visible = [c["name"] for c in columns if not c["hidden"]]
            searchable = [c["name"] for c in columns if not c["hidden"] and not c["data_type"].endswith(("blob", "binary"))]
            primary = meta["primary_key"]
            order_by = primary or columns[0]["name"]
            descending = bool(primary and next(c for c in columns if c["name"] == primary)["auto"])
            rows, total = repo.page(name, visible, searchable, order_by, descending, (term or "").strip() or None, limit, offset)
        return {
            **meta,
            "rows": [{key: to_json_value(value) for key, value in row.items()} for row in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    # ------------------------------------------------------------ row changes
    def insert_row(self, admin: User, name: str, values: dict[str, Any]) -> dict[str, Any]:
        with admin_session(self._db) as session:
            repo = DatabaseAdminRepository(session)
            meta = self._describe(repo, name)
            self._writable(meta)
            if not meta["can_insert"]:
                raise ConflictError("Add accounts from the Users page, so the password is hashed.")
            new_id = repo.insert(name, self._clean(meta, values, inserting=True))
            AuditRepository(session).record(admin.id, "DB_INSERT_ROW", name[:50], new_id or None, f"Added a row to {name}")
        return {"ok": True, "id": new_id}

    def update_row(self, admin: User, name: str, key: str, values: dict[str, Any]) -> dict[str, Any]:
        with admin_session(self._db) as session:
            repo = DatabaseAdminRepository(session)
            meta = self._describe(repo, name)
            self._writable(meta)
            primary = meta["primary_key"]
            if not repo.row_exists(name, primary, key):
                raise NotFoundError("Row not found.")
            data = self._clean(meta, values, inserting=False)
            if not data:
                raise ValidationFailedError("Nothing was changed.")
            if name == "users" and key == str(admin.id) and ({"role", "is_active"} & set(data)):
                raise PermissionDeniedError("You cannot change your own role or active status here.")
            repo.update_row(name, primary, key, data)
            AuditRepository(session).record(
                admin.id, "DB_UPDATE_ROW", name[:50], int(key) if key.isdigit() else None, f"Edited a row in {name}"
            )
        return {"ok": True}

    def delete_row(self, admin: User, name: str, key: str) -> dict[str, Any]:
        with admin_session(self._db) as session:
            repo = DatabaseAdminRepository(session)
            meta = self._describe(repo, name)
            self._writable(meta)
            primary = meta["primary_key"]
            if name == "users" and key == str(admin.id):
                raise PermissionDeniedError("You cannot delete your own account.")
            if not repo.row_exists(name, primary, key):
                raise NotFoundError("Row not found.")
            repo.delete_row(name, primary, key)
            AuditRepository(session).record(
                admin.id, "DB_DELETE_ROW", name[:50], int(key) if key.isdigit() else None, f"Deleted a row from {name}"
            )
        return {"ok": True}

    # ------------------------------------------------------------ SQL console
    def run_sql(self, admin: User, sql: str) -> dict[str, Any]:
        """Run one statement. Reads return rows. INSERT, UPDATE and DELETE commit together with their audit entry."""
        text = sql.strip().rstrip(";").strip()
        if not text:
            raise ValidationFailedError("Type a statement first.")
        if ";" in text:
            raise ValidationFailedError("Run one statement at a time (remove the semicolon in the middle).")
        match = re.match(r"(?is)^\s*(select|show|describe|desc|explain|insert|update|delete)\b", text)
        if match is None:
            raise ValidationFailedError(
                "Only SELECT, SHOW, DESCRIBE, EXPLAIN, INSERT, UPDATE and DELETE are allowed. "
                "Changing the table structure needs the MySQL root account."
            )
        kind = match.group(1).lower()

        if kind in _READ_KINDS:
            with admin_session(self._db) as session:
                session.update("SET SESSION MAX_EXECUTION_TIME = 5000")  # a slow query cannot hold a connection forever
                names, rows = session.select(text)
            hidden = {i for i, n in enumerate(names) if n.lower() in _HIDDEN}
            shown = rows[:_CONSOLE_LIMIT]
            return {
                "kind": kind,
                "columns": names,
                "rows": [["(hidden)" if i in hidden else to_json_value(v) for i, v in enumerate(row)] for row in shown],
                "truncated": len(rows) > _CONSOLE_LIMIT,
                "affected": None,
            }

        if re.search(r"\baudit_logs\b", text, re.IGNORECASE):
            raise PermissionDeniedError("The audit log is append-only and cannot be changed.")
        if kind in ("update", "delete") and not re.search(r"\bwhere\b", text, re.IGNORECASE):
            raise ValidationFailedError("UPDATE and DELETE need a WHERE clause, so a whole table is never changed by accident.")
        with admin_session(self._db) as session:
            affected = session.update(text)
            AuditRepository(session).record(admin.id, "DB_RUN_SQL", "database", None, f"{kind.upper()} statement changed {affected} row(s)")
        return {"kind": kind, "columns": [], "rows": [], "truncated": False, "affected": affected}

    # ------------------------------------------------------------ backup
    def backup(self, admin: User) -> tuple[str, str]:
        """Returns (file name, SQL text) for the whole database, and records the download."""
        with admin_session(self._db) as session:
            content, summary = DatabaseAdminRepository(session).dump()
            stamp = session.server_now()
            AuditRepository(session).record(admin.id, "BACKUP_DATABASE", "database", None, f"Downloaded a backup ({summary})")
        return f"appointmed-backup_{stamp:%Y-%m-%d_%H%M}.sql", content