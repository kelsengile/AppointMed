"""Public staff directory for the front page (names and roles only, no contact details)."""

from __future__ import annotations

from collections import defaultdict

from backend.core.database import Row

from .base_repository import BaseRepository


_PHOTO = "(u.avatar IS NOT NULL) AS has_photo, COALESCE(LENGTH(u.avatar), 0) AS photo_version"


class StaffDirectoryRepository(BaseRepository):
    """Read-only list of active staff accounts."""

    table = "users"
    columns = ()

    @staticmethod
    def _photo_fields(row: Row) -> None:
        row["has_photo"] = bool(row["has_photo"])
        row["photo_version"] = int(row["photo_version"])

    def _weekdays(self, doctor_ids: list[int] | None = None) -> dict[int, list[int]]:
        days: dict[int, list[int]] = defaultdict(list)
        for row in self._db.fetch_all("SELECT doctor_id, weekday FROM doctor_schedules ORDER BY weekday"):
            if row["weekday"] not in days[row["doctor_id"]]:
                days[row["doctor_id"]].append(row["weekday"])
        return days

    def list_active(self) -> list[Row]:
        """Active doctors, then nurses, then admins. Doctors include the weekdays they work.

        Only safe fields are returned: no username, email, password hash or login times.
        """
        staff = self._db.fetch_all(
            f"""
            SELECT u.id, u.full_name, u.role, u.specialization, u.assigned_doctor_id,
                   d.full_name AS assigned_doctor_name, {_PHOTO}
            FROM users u
            LEFT JOIN users d ON d.id = u.assigned_doctor_id
            WHERE u.is_active = 1
            ORDER BY FIELD(u.role, 'doctor', 'nurse', 'admin'), u.full_name
            """
        )
        days = self._weekdays()
        for member in staff:
            self._photo_fields(member)
            member["weekdays"] = days.get(member["id"], []) if member["role"] == "doctor" else []
        return staff

    def get_active(self, staff_id: int) -> Row | None:
        """One active staff member with the public profile text, and the nurses of a doctor."""
        row = self._db.fetch_one(
            f"""
            SELECT u.id, u.full_name, u.role, u.specialization, u.assigned_doctor_id,
                   d.full_name AS assigned_doctor_name,
                   u.bio, u.education, u.years_experience, u.languages, {_PHOTO}
            FROM users u
            LEFT JOIN users d ON d.id = u.assigned_doctor_id
            WHERE u.is_active = 1 AND u.id = %s
            """,
            (staff_id,),
        )
        if row is None:
            return None
        self._photo_fields(row)
        row["weekdays"] = []
        row["nurses"] = []
        if row["role"] == "doctor":
            row["weekdays"] = self._weekdays().get(staff_id, [])
            nurses = self._db.fetch_all(
                f"SELECT u.id, u.full_name, {_PHOTO} FROM users u "
                "WHERE u.role = 'nurse' AND u.is_active = 1 AND u.assigned_doctor_id = %s ORDER BY u.full_name",
                (staff_id,),
            )
            for nurse in nurses:
                self._photo_fields(nurse)
            row["nurses"] = nurses
        return row

    def photo(self, staff_id: int) -> bytes | None:
        """The profile picture of an active staff member."""
        row = self._db.fetch_one("SELECT avatar FROM users WHERE id = %s AND is_active = 1", (staff_id,))
        return bytes(row["avatar"]) if row and row["avatar"] else None