"""Staff directory for the public front page."""

from __future__ import annotations

from backend.core.database import Database, Row, database
from backend.repositories.staff_directory_repository import StaffDirectoryRepository


class StaffDirectoryService:
    """Read-only access to the list of clinic staff (no login needed)."""

    def __init__(self, db: Database = database) -> None:
        self._db = db

    def list_public(self) -> list[Row]:
        """Every active staff account with public-safe fields only."""
        return StaffDirectoryRepository(self._db).list_active()