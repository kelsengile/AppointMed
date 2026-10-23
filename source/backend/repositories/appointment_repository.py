"""Appointments and booking requests (notifications)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from backend.core.database import Row

from .base_repository import BaseRepository, placeholders

_APPT_SELECT = """
SELECT a.id, a.patient_id, a.full_name, a.doctor_id, d.full_name AS doctor_name, a.nurse_id,
       a.room_id, r.room_name, a.source, a.scheduled_time, a.reason, a.status, a.checked_in_at, a.notification_id,
       COALESCE(p.birthdate, n.birthdate) AS birthdate,
       COALESCE(p.sex, n.sex) AS sex,
       COALESCE(p.contact_number, n.contact_number) AS contact_number,
       i.id AS invoice_id, i.consultation_fee, i.amount AS invoice_amount, i.status AS invoice_status
FROM appointments a
JOIN users d ON d.id = a.doctor_id
LEFT JOIN rooms r ON r.id = a.room_id
LEFT JOIN patients p ON p.id = a.patient_id
LEFT JOIN notifications n ON n.id = a.notification_id
LEFT JOIN invoices i ON i.appointment_id = a.id
"""


class AppointmentRepository(BaseRepository):
    """Queries for the appointments table."""

    table = "appointments"
    columns = (
        "notification_id", "patient_id", "full_name", "doctor_id", "nurse_id", "room_id",
        "source", "scheduled_time", "reason", "status", "checked_in_at",
    )

    def get_item(self, appointment_id: int) -> Row | None:
        """One appointment with patient, room and invoice details."""
        return self._db.fetch_one(_APPT_SELECT + " WHERE a.id = %s", (appointment_id,))

    def list_for_doctor(
        self, doctor_id: int, when: str | date = "today", term: str | None = None, statuses: list[str] | None = None
    ) -> list[Row]:
        """A doctor's appointments for 'today', 'upcoming', 'all' or one date."""
        conditions, params = ["a.doctor_id = %s"], [doctor_id]
        if when == "today":
            conditions.append("DATE(a.scheduled_time) = CURDATE()")
        elif when == "upcoming":
            conditions.append("a.scheduled_time >= CURDATE()")
        elif isinstance(when, date):
            conditions.append("DATE(a.scheduled_time) = %s")
            params.append(when)  # type: ignore[arg-type]
        elif when != "all":
            raise ValueError("Unknown day filter")
        if term:
            conditions.append("(a.full_name LIKE %s OR a.reason LIKE %s)")
            params += [f"%{term}%", f"%{term}%"]
        if statuses:
            conditions.append(f"a.status IN ({placeholders(len(statuses))})")
            params += statuses
        return self._db.fetch_all(_APPT_SELECT + " WHERE " + " AND ".join(conditions) + " ORDER BY a.scheduled_time, a.id", params)

    def queue(self, doctor_id: int) -> list[Row]:
        """Checked-in patients (unordered; the WaitingQueue orders them)."""
        return self._db.fetch_all(_APPT_SELECT + " WHERE a.doctor_id = %s AND a.status = 'Checked-in'", (doctor_id,))

    def consulting(self, doctor_id: int, exclude_id: int | None = None) -> Row | None:
        """The appointment currently in the doctor's exam room, if any."""
        return self._db.fetch_one(
            _APPT_SELECT + " WHERE a.doctor_id = %s AND a.status = 'Consulting' AND a.id <> %s LIMIT 1",
            (doctor_id, exclude_id or 0),
        )

    def unbilled(self, doctor_id: int) -> list[Row]:
        """Examined appointments that still have no invoice."""
        return self._db.fetch_all(
            _APPT_SELECT + " WHERE a.doctor_id = %s AND a.status = 'Examined' AND i.id IS NULL ORDER BY a.scheduled_time",
            (doctor_id,),
        )

    def conflict_exists(self, doctor_id: int, when: datetime, exclude_id: int | None = None) -> bool:
        """True when the doctor already has a non-cancelled appointment at exactly this time."""
        row = self._db.fetch_one(
            "SELECT 1 AS hit FROM appointments WHERE doctor_id = %s AND scheduled_time = %s AND status <> 'Cancelled' AND id <> %s LIMIT 1",
            (doctor_id, when, exclude_id or 0),
        )
        return row is not None

    def booked_times(self, doctor_id: int, day: date) -> set[datetime]:
        """Times on a day that are taken by appointments or by pending requests."""
        rows = self._db.fetch_all(
            """
            SELECT scheduled_time AS taken FROM appointments
              WHERE doctor_id = %s AND DATE(scheduled_time) = %s AND status <> 'Cancelled'
            UNION
            SELECT preferred_datetime AS taken FROM notifications
              WHERE doctor_id = %s AND status = 'Pending' AND preferred_datetime IS NOT NULL AND DATE(preferred_datetime) = %s
            """,
            (doctor_id, day, doctor_id, day),
        )
        return {r["taken"] for r in rows}

    def status_counts_today(self, doctor_id: int) -> list[Row]:
        return self._db.fetch_all(
            "SELECT status, COUNT(*) AS n FROM appointments WHERE doctor_id = %s AND DATE(scheduled_time) = CURDATE() GROUP BY status",
            (doctor_id,),
        )


class NotificationRepository(BaseRepository):
    """Booking requests routed to a doctor and a nurse."""

    table = "notifications"
    columns = (
        "doctor_id", "nurse_id", "requester_name", "contact_number", "email", "birthdate", "sex", "address",
        "preferred_datetime", "reason", "origin", "status", "decision_note", "decided_by", "resolved_at",
    )

    def list_for_doctor(self, doctor_id: int, status: str | None = None) -> list[Row]:
        """Requests for a doctor, pending first. `slot_taken` warns when the wanted time is already booked."""
        sql = """
            SELECT n.id, n.doctor_id, n.requester_name, n.contact_number, n.email, n.birthdate, n.sex, n.address,
                   n.preferred_datetime, n.reason, n.origin, n.status, n.decision_note, n.created_at, n.resolved_at,
                   EXISTS(SELECT 1 FROM appointments a WHERE a.doctor_id = n.doctor_id
                          AND a.scheduled_time = n.preferred_datetime AND a.status <> 'Cancelled') AS slot_taken
            FROM notifications n WHERE n.doctor_id = %s
        """
        params: list[Any] = [doctor_id]
        if status:
            sql += " AND n.status = %s"
            params.append(status)
        sql += " ORDER BY (n.status = 'Pending') DESC, n.created_at DESC, n.id DESC"
        rows = self._db.fetch_all(sql, params)
        for row in rows:
            row["slot_taken"] = bool(row["slot_taken"])
        return rows

    def resolve(self, notification_id: int, status: str, note: str | None, user_id: int) -> int:
        """Mark a pending request as Converted or Dismissed. Returns 0 if it was no longer pending."""
        return self._db.update(
            "UPDATE notifications SET status = %s, decision_note = %s, decided_by = %s, resolved_at = NOW() "
            "WHERE id = %s AND status = 'Pending'",
            (status, note, user_id, notification_id),
        )

    def count_pending(self, doctor_id: int) -> int:
        row = self._db.fetch_one("SELECT COUNT(*) AS n FROM notifications WHERE doctor_id = %s AND status = 'Pending'", (doctor_id,))
        return int(row["n"]) if row else 0