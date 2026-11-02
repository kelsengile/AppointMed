"""Abstract base for repositories. Only repositories contain SQL."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.core.database import Executor, Row


def placeholders(count: int) -> str:
    """'%s, %s, %s' for building IN (...) lists safely."""
    return ", ".join(["%s"] * count)


class BaseRepository(ABC):
    """Generic get/create/update/delete for one table. Column names come from a fixed whitelist."""

    select_columns = "*"

    def __init__(self, db: Executor) -> None:
        self._db = db

    @property
    @abstractmethod
    def table(self) -> str:
        """Name of the table this repository owns."""

    @property
    @abstractmethod
    def columns(self) -> tuple[str, ...]:
        """Columns that may be written through create() and update()."""

    def _allowed(self, data: dict[str, Any]) -> list[str]:
        unknown = [key for key in data if key not in self.columns]
        if unknown:
            raise ValueError(f"Columns not allowed for {self.table}: {unknown}")
        return list(data)

    def get(self, record_id: int) -> Row | None:
        """Fetch one record by id."""
        return self._db.fetch_one(f"SELECT {self.select_columns} FROM {self.table} WHERE id = %s", (record_id,))

    def create(self, data: dict[str, Any]) -> int:
        """Insert a record and return its new id."""
        cols = self._allowed(data)
        sql = f"INSERT INTO {self.table} ({', '.join(cols)}) VALUES ({placeholders(len(cols))})"
        return self._db.execute(sql, [data[c] for c in cols])

    def update(self, record_id: int, data: dict[str, Any]) -> int:
        """Update the given columns of one record. Returns rows changed."""
        cols = self._allowed(data)
        if not cols:
            return 0
        assignments = ", ".join(f"{c} = %s" for c in cols)
        return self._db.update(f"UPDATE {self.table} SET {assignments} WHERE id = %s", [*(data[c] for c in cols), record_id])

    def delete(self, record_id: int) -> int:
        """Delete one record. Returns rows removed."""
        return self._db.update(f"DELETE FROM {self.table} WHERE id = %s", (record_id,))