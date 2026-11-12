"""Staff directory for the public front page and the staff profile page."""

from __future__ import annotations

from backend.core.database import Database, Row, database
from backend.core.exceptions import NotFoundError
from backend.repositories.staff_directory_repository import StaffDirectoryRepository
from backend.services.auth_service import _detect_mime


class StaffDirectoryService:
    """Read-only access to the clinic staff (no login needed)."""

    def __init__(self, db: Database = database) -> None:
        self._db = db

    def list_public(self) -> list[Row]:
        """Every active staff account with public-safe fields only."""
        return StaffDirectoryRepository(self._db).list_active()

    def get_public(self, staff_id: int) -> Row:
        row = StaffDirectoryRepository(self._db).get_active(staff_id)
        if row is None:
            raise NotFoundError("Staff member not found.")
        return row

    def photo(self, staff_id: int) -> tuple[bytes, str]:
        raw = StaffDirectoryRepository(self._db).photo(staff_id)
        mime = _detect_mime(raw) if raw else None
        if not raw or not mime:
            raise NotFoundError("No photo.")
        return raw, mime