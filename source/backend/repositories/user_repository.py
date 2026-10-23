"""SQL for users, doctor schedules, clinic settings, and the audit log."""

from datetime import timedelta

from backend.core.database import Session

USER_COLUMNS = "id, username, full_name, role, email, specialization, assigned_doctor_id, is_active"


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def get(self, user_id: int) -> dict | None:
        return self._s.one(f"SELECT {USER_COLUMNS} FROM users WHERE id = %s", (user_id,))

    def get_by_username(self, username: str) -> dict | None:
        return self._s.one(f"SELECT {USER_COLUMNS}, password_hash FROM users WHERE username = %s", (username,))

    def record_login(self, user_id: int) -> None:
        self._s.execute("UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = %s", (user_id,))

    def lock(self, user_id: int) -> None:
        """Lock the user row so two requests for the same doctor run one after the other."""
        self._s.one("SELECT id FROM users WHERE id = %s FOR UPDATE", (user_id,))

    def bookable_doctors(self) -> list[dict]:
        return self._s.all(
            "SELECT id, full_name, specialization FROM users "
            "WHERE role = 'doctor' AND is_active = TRUE ORDER BY full_name"
        )

    def nurse_for_doctor(self, doctor_id: int) -> int | None:
        row = self._s.one(
            "SELECT id FROM users WHERE role = 'nurse' AND is_active = TRUE "
            "AND assigned_doctor_id = %s ORDER BY id LIMIT 1",
            (doctor_id,),
        )
        return row["id"] if row else None


class ScheduleRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def blocks_for(self, doctor_id: int, weekday: int) -> list[dict]:
        return self._s.all(
            "SELECT start_time, end_time, slot_minutes FROM doctor_schedules "
            "WHERE doctor_id = %s AND weekday = %s ORDER BY start_time",
            (doctor_id, weekday),
        )

    def weekdays_by_doctor(self) -> dict[int, list[int]]:
        rows = self._s.all(
            "SELECT doctor_id, weekday FROM doctor_schedules GROUP BY doctor_id, weekday ORDER BY weekday"
        )
        result: dict[int, list[int]] = {}
        for row in rows:
            result.setdefault(row["doctor_id"], []).append(row["weekday"])
        return result


def as_delta(value) -> timedelta:
    """MySQL TIME columns arrive as timedelta; convert a time object if needed."""
    if isinstance(value, timedelta):
        return value
    return timedelta(hours=value.hour, minutes=value.minute, seconds=value.second)


class SettingsRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def get(self, key: str, default: str = "") -> str:
        row = self._s.one("SELECT setting_value FROM clinic_settings WHERE setting_key = %s", (key,))
        return row["setting_value"] if row else default

    def get_bool(self, key: str, default: bool = True) -> bool:
        value = self.get(key, "true" if default else "false")
        return value.strip().lower() in ("1", "true", "yes", "on")


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def log(
        self,
        user_id: int | None,
        action: str,
        entity: str | None = None,
        entity_id: int | None = None,
        details: str | None = None,
    ) -> None:
        """Append one row. Never pass passwords or medical details."""
        self._s.execute(
            "INSERT INTO audit_logs (user_id, action, entity, entity_id, details) VALUES (%s, %s, %s, %s, %s)",
            (user_id, action, entity, entity_id, details[:255] if details else None),
        )