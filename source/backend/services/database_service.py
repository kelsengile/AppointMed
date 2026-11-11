"""Database page: browse and edit table rows, run one SQL statement, and download a backup.

Only administrators reach this (feature "database"). Every change is written to the audit log
(without the values, so no personal or medical data ends up there).
"""

from __future__ import annotations

import re
from typing import Any

from backend.core.database import Database, database
from backend.core.exceptions import AppError, ConflictError, NotFoundError, PermissionDeniedError, ValidationFailedError
from backend.services.backup_parser import parse_backup
from backend.models.domain import User
from backend.repositories.database_repository import DatabaseAdminRepository, admin_session, to_json_value
from backend.repositories.system_repository import AuditRepository
from backend.services.notifier import Notifier, notifier

_HIDDEN = frozenset({"password_hash", "avatar"})  # never shown in the browser or the console
_READ_ONLY = frozenset({"audit_logs"})  # the audit log is append-only
_NO_INSERT = frozenset({"users"})  # new accounts need a hashed password: use the Users page
_TEXT_TYPES = frozenset({"char", "varchar", "tinytext", "text", "mediumtext", "longtext"})
_READ_KINDS = frozenset({"select", "show", "describe", "desc", "explain"})
_CONSOLE_LIMIT = 500
_KEEP_ON_IMPORT = frozenset({"audit_logs"})  # append-only, so an import never replaces it

class DatabaseService:
    """Rules for the administrator's database tools."""

    def __init__(self, db: Database = database, notify: Notifier = notifier) -> None:
        self._db = db
        self._notifier = notify

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
        self._notifier.database_event(
            actor_id=admin.id,
            actor_name=admin.full_name,
            title="A database backup was downloaded",
            detail=summary,
        )
        return f"appointmed-backup_{stamp:%Y-%m-%d_%H%M}.sql", content

        # ------------------------------------------------------------ import
    def import_backup(self, admin: User, content: str) -> dict[str, Any]:
        """Replace the rows of every table with the rows in a backup file (structure is not changed)."""
        parsed = parse_backup(content)  # nothing touches the database until the file is understood
        with admin_session(self._db) as session:
            repo = DatabaseAdminRepository(session)
            existing = repo.table_names()
            unknown = sorted(parsed.tables - set(existing))
            if unknown:
                raise ValidationFailedError(f"The backup has tables this database does not have: {', '.join(unknown)}.")
            missing = [name for name in existing if name not in parsed.tables]
            if missing:
                raise ValidationFailedError(f"The backup is incomplete. It is missing: {', '.join(missing)}.")
            allowed = {name: {c["name"] for c in repo.columns(name) if not c["generated"]} for name in existing}
            for table, columns, _ in parsed.inserts:
                bad = [c for c in columns if c not in allowed[table]]
                if bad:
                    raise ValidationFailedError(f"The backup has columns that {table} does not have: {', '.join(bad)}.")

            targets = [name for name in existing if name not in _KEEP_ON_IMPORT]
            total = 0
            repo.set_foreign_key_checks(False)
            try:
                for name in targets:
                    repo.clear_table(name)
                for table, columns, rows in parsed.inserts:
                    if table in _KEEP_ON_IMPORT:
                        continue
                    try:
                        total += repo.insert_many(table, columns, rows)
                    except (ValidationFailedError, ConflictError) as exc:
                        raise ValidationFailedError(f"Could not import into {table}: {exc.message}") from exc
                if not repo.is_active_admin(admin.id):
                    raise ConflictError(
                        "The backup does not contain your own active administrator account, so nothing was changed."
                    )
            finally:
                try:
                    repo.set_foreign_key_checks(True)
                except AppError:
                    pass
            AuditRepository(session).record(
                admin.id, "RESTORE_DATABASE", "database", None, f"Imported a backup ({len(targets)} tables, {total} rows)"
            )
        self._notifier.database_event(
            actor_id=admin.id,
            actor_name=admin.full_name,
            title="The database was restored from a backup",
            detail=f"{len(targets)} tables, {total} rows",
        )
        return {"ok": True, "tables": len(targets), "rows": total}