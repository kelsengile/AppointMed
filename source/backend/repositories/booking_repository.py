"""SQL for booking requests (notifications) and patient records."""

from datetime import date, datetime

from backend.core.database import Session

NOTIFICATION_COLUMNS = (
    "id, doctor_id, nurse_id, requester_name, contact_number, email, birthdate, sex, address, "
    "preferred_datetime, reason, origin, status, decision_note, decided_by, created_at, resolved_at"
)


class NotificationRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, doctor_id: int, nurse_id: int | None, data: dict) -> int:
        return self._s.execute(
            "INSERT INTO notifications (doctor_id, nurse_id, requester_name, contact_number, email, "
            "birthdate, sex, address, preferred_datetime, reason) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                doctor_id,
                nurse_id,
                data["full_name"],
                data["contact_number"],
                data["email"],
                data["birthdate"],
                data["sex"],
                data["address"],
                data["preferred_datetime"],
                data["reason"],
            ),
        )

    def get(self, notification_id: int, for_update: bool = False) -> dict | None:
        sql = f"SELECT {NOTIFICATION_COLUMNS} FROM notifications WHERE id = %s"
        return self._s.one(sql + (" FOR UPDATE" if for_update else ""), (notification_id,))

    def pending_slots(self, doctor_id: int, start: datetime, end: datetime) -> list[datetime]:
        rows = self._s.all(
            "SELECT preferred_datetime FROM notifications WHERE doctor_id = %s AND status = 'Pending' "
            "AND preferred_datetime >= %s AND preferred_datetime < %s",
            (doctor_id, start, end),
        )
        return [row["preferred_datetime"] for row in rows]

    def for_doctor(self, doctor_id: int, status: str | None) -> list[dict]:
        sql = f"SELECT {NOTIFICATION_COLUMNS} FROM notifications WHERE doctor_id = %s"
        params: list = [doctor_id]
        if status:
            sql += " AND status = %s"
            params.append(status)
        sql += " ORDER BY (status = 'Pending') DESC, created_at DESC LIMIT 200"
        return self._s.all(sql, params)

    def resolve(self, notification_id: int, status: str, user_id: int, note: str | None) -> None:
        self._s.execute(
            "UPDATE notifications SET status = %s, resolved_at = %s, decided_by = %s, decision_note = %s "
            "WHERE id = %s",
            (status, datetime.now(), user_id, note, notification_id),
        )


class PatientRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def find_match(self, full_name: str, birthdate: date | None) -> int | None:
        """A returning patient has the same name and birthdate (NULL-safe comparison)."""
        row = self._s.one(
            "SELECT id FROM patients WHERE full_name = %s AND birthdate <=> %s LIMIT 1", (full_name, birthdate)
        )
        return row["id"] if row else None

    def create(self, data: dict) -> int:
        return self._s.execute(
            "INSERT INTO patients (full_name, birthdate, sex, contact_number, email, address, "
            "condition_summary, doctor_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (
                data["full_name"],
                data.get("birthdate"),
                data.get("sex"),
                data.get("contact_number"),
                data.get("email"),
                data.get("address"),
                (data.get("condition_summary") or "")[:255] or None,
                data.get("doctor_id"),
            ),
        )

    def update_contact(self, patient_id: int, contact: str | None, email: str | None, address: str | None) -> None:
        self._s.execute(
            "UPDATE patients SET contact_number = COALESCE(%s, contact_number), "
            "email = COALESCE(%s, email), address = COALESCE(%s, address) WHERE id = %s",
            (contact, email, address, patient_id),
        )

    def set_condition(self, patient_id: int, summary: str) -> None:
        self._s.execute("UPDATE patients SET condition_summary = %s WHERE id = %s", (summary[:255], patient_id))

    def search(self, doctor_id: int, term: str) -> list[dict]:
        return self._s.all(
            "SELECT p.id, p.full_name, p.birthdate, p.sex, p.contact_number, p.email, p.address, "
            "p.condition_summary, "
            "(SELECT COUNT(*) FROM appointments a WHERE a.patient_id = p.id AND a.doctor_id = %s "
            " AND a.status = 'Completed') AS visit_count "
            "FROM patients p "
            "WHERE (p.doctor_id = %s OR EXISTS "
            "  (SELECT 1 FROM appointments a2 WHERE a2.patient_id = p.id AND a2.doctor_id = %s)) "
            "AND p.full_name LIKE %s ORDER BY p.full_name LIMIT 200",
            (doctor_id, doctor_id, doctor_id, f"%{term}%"),
        )