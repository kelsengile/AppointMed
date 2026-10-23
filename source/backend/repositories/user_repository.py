"""Users (staff accounts) and doctor schedules."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time, timedelta
from typing import Any

from backend.core.database import Row

from .base_repository import BaseRepository, placeholders

_PUBLIC = "id, username, full_name, role, email, specialization, assigned_doctor_id, is_active, last_login_at, created_at"
_LISTING = """
SELECT u.id, u.username, u.full_name, u.role, u.email, u.specialization, u.assigned_doctor_id,
       d.full_name AS assigned_doctor_name, u.is_active, u.last_login_at, u.created_at
FROM users u LEFT JOIN users d ON d.id = u.assigned_doctor_id
"""


def _as_time(value: Any) -> time:
    """MySQL TIME columns arrive as timedelta; convert to datetime.time."""
    if isinstance(value, timedelta):
        return (datetime.min + value).time()
    return value


def _clean(row: Row | None) -> Row | None:
    if row is not None:
        row["is_active"] = bool(row["is_active"])
    return row


class UserRepository(BaseRepository):
    """Queries for the users table. Password hashes are only returned by dedicated methods."""

    table = "users"
    columns = ("username", "password_hash", "full_name", "role", "email", "specialization", "assigned_doctor_id", "is_active")
    select_columns = _PUBLIC

    def get(self, record_id: int) -> Row | None:
        return _clean(super().get(record_id))

    def get_detail(self, user_id: int) -> Row | None:
        """One user with the assigned doctor's name (for admin screens and the profile page)."""
        return _clean(self._db.fetch_one(_LISTING + " WHERE u.id = %s", (user_id,)))

    def get_by_username(self, username: str) -> Row | None:
        """Used by login only: includes the password hash."""
        return _clean(self._db.fetch_one(f"SELECT {_PUBLIC}, password_hash FROM users WHERE username = %s", (username,)))

    def get_password_hash(self, user_id: int) -> str | None:
        row = self._db.fetch_one("SELECT password_hash FROM users WHERE id = %s", (user_id,))
        return row["password_hash"] if row else None

    def list_users(self, role: str | None = None, term: str | None = None) -> list[Row]:
        """All users, optionally filtered by role and a name/username search."""
        conditions, params = ["1 = 1"], []
        if role:
            conditions.append("u.role = %s")
            params.append(role)
        if term:
            conditions.append("(u.full_name LIKE %s OR u.username LIKE %s)")
            params += [f"%{term}%", f"%{term}%"]
        rows = self._db.fetch_all(_LISTING + " WHERE " + " AND ".join(conditions) + " ORDER BY u.role, u.full_name", params)
        return [_clean(r) for r in rows]  # type: ignore[misc]

    def touch_login(self, user_id: int) -> None:
        self._db.update("UPDATE users SET last_login_at = NOW() WHERE id = %s", (user_id,))

    def set_password(self, user_id: int, password_hash: str) -> None:
        self._db.update("UPDATE users SET password_hash = %s WHERE id = %s", (password_hash, user_id))

    def get_avatar(self, user_id: int) -> bytes | None:
        row = self._db.fetch_one("SELECT avatar FROM users WHERE id = %s", (user_id,))
        return bytes(row["avatar"]) if row and row["avatar"] else None

    def set_avatar(self, user_id: int, image: bytes | None) -> None:
        self._db.update("UPDATE users SET avatar = %s WHERE id = %s", (image, user_id))

    def public_doctors(self) -> list[Row]:
        """Active doctors who have a schedule, with the weekdays they work (for the booking page)."""
        doctors = self._db.fetch_all(
            "SELECT id, full_name, specialization FROM users WHERE role = 'doctor' AND is_active = 1 ORDER BY full_name"
        )
        days: dict[int, list[int]] = defaultdict(list)
        for row in self._db.fetch_all("SELECT doctor_id, weekday FROM doctor_schedules ORDER BY weekday"):
            if row["weekday"] not in days[row["doctor_id"]]:
                days[row["doctor_id"]].append(row["weekday"])
        for doctor in doctors:
            doctor["weekdays"] = days.get(doctor["id"], [])
        return [d for d in doctors if d["weekdays"]]

    def nurses_for_doctor(self, doctor_id: int) -> list[Row]:
        """Active nurses assigned to a doctor, the one with the fewest pending requests first."""
        return self._db.fetch_all(
            """
            SELECT u.id, u.full_name, COUNT(n.id) AS pending
            FROM users u LEFT JOIN notifications n ON n.nurse_id = u.id AND n.status = 'Pending'
            WHERE u.role = 'nurse' AND u.is_active = 1 AND u.assigned_doctor_id = %s
            GROUP BY u.id, u.full_name ORDER BY pending, u.id
            """,
            (doctor_id,),
        )

    def active_doctors(self) -> list[Row]:
        return self._db.fetch_all("SELECT id, full_name FROM users WHERE role = 'doctor' AND is_active = 1 ORDER BY full_name")


class ScheduleRepository(BaseRepository):
    """Weekly working hours for doctors."""

    table = "doctor_schedules"
    columns = ("doctor_id", "weekday", "start_time", "end_time", "slot_minutes")

    def blocks_for_day(self, doctor_id: int, weekday: int) -> list[Row]:
        """Working blocks on one ISO weekday (times as datetime.time)."""
        rows = self._db.fetch_all(
            "SELECT start_time, end_time, slot_minutes FROM doctor_schedules WHERE doctor_id = %s AND weekday = %s ORDER BY start_time",
            (doctor_id, weekday),
        )
        for row in rows:
            row["start_time"], row["end_time"] = _as_time(row["start_time"]), _as_time(row["end_time"])
        return rows

    def blocks_for_doctor(self, doctor_id: int) -> list[Row]:
        """All blocks, with times as 'HH:MM' strings ready for JSON."""
        rows = self._db.fetch_all(
            "SELECT weekday, start_time, end_time, slot_minutes FROM doctor_schedules WHERE doctor_id = %s ORDER BY weekday, start_time",
            (doctor_id,),
        )
        return [
            {
                "weekday": r["weekday"],
                "start_time": _as_time(r["start_time"]).strftime("%H:%M"),
                "end_time": _as_time(r["end_time"]).strftime("%H:%M"),
                "slot_minutes": r["slot_minutes"],
            }
            for r in rows
        ]

    def replace(self, doctor_id: int, blocks: list[dict[str, Any]]) -> None:
        """Replace a doctor's whole weekly schedule (call inside a transaction)."""
        self._db.update("DELETE FROM doctor_schedules WHERE doctor_id = %s", (doctor_id,))
        for block in blocks:
            self.create({"doctor_id": doctor_id, **block})


__all__ = ["UserRepository", "ScheduleRepository", "placeholders"]