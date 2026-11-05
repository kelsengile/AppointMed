"""Public staff directory for the front page (names and roles only, no contact details)."""

from __future__ import annotations

from collections import defaultdict

from backend.core.database import Row

from .base_repository import BaseRepository


class StaffDirectoryRepository(BaseRepository):
    """Read-only list of active staff accounts."""

    table = "users"
    columns = ()

    def list_active(self) -> list[Row]:
        """Active doctors, then nurses, then admins. Doctors include the weekdays they work.

        Only safe fields are returned: no username, email, password hash or login times.
        """
        staff = self._db.fetch_all(
            """
            SELECT u.id, u.full_name, u.role, u.specialization, d.full_name AS assigned_doctor_name
            FROM users u
            LEFT JOIN users d ON d.id = u.assigned_doctor_id
            WHERE u.is_active = 1
            ORDER BY FIELD(u.role, 'doctor', 'nurse', 'admin'), u.full_name
            """
        )
        days: dict[int, list[int]] = defaultdict(list)
        for row in self._db.fetch_all("SELECT doctor_id, weekday FROM doctor_schedules ORDER BY weekday"):
            if row["weekday"] not in days[row["doctor_id"]]:
                days[row["doctor_id"]].append(row["weekday"])
        for member in staff:
            member["weekdays"] = days.get(member["id"], []) if member["role"] == "doctor" else []
        return staff