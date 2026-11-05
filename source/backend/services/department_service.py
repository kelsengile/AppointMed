"""Departments for the public front page."""

from __future__ import annotations

from backend.core.database import Database, Row, database
from backend.repositories.department_repository import DepartmentRepository


class DepartmentService:
    """Read-only access to the clinic's departments (no login needed)."""

    def __init__(self, db: Database = database) -> None:
        self._db = db

    def list_public(self) -> list[Row]:
        """Every active department, featured ones first."""
        return DepartmentRepository(self._db).list_active()