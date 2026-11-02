"""Rooms, clinic settings, audit logs, and report queries."""

from __future__ import annotations

from datetime import date
from typing import Any

from backend.core.database import Row

from .base_repository import BaseRepository


class RoomRepository(BaseRepository):
    """Exam rooms."""

    table = "rooms"
    columns = ("room_name", "status", "updated_by")

    def list_with_occupant(self) -> list[Row]:
        """Rooms with who last changed them and the patient currently inside, if any."""
        return self._db.fetch_all(
            "SELECT r.id, r.room_name, r.status, r.updated_at, u.full_name AS updated_by_name, "
            "(SELECT a.full_name FROM appointments a WHERE a.room_id = r.id AND a.status = 'Consulting' LIMIT 1) AS occupant "
            "FROM rooms r LEFT JOIN users u ON u.id = r.updated_by ORDER BY r.room_name"
        )

    def in_use(self, room_id: int) -> bool:
        """True when any appointment references the room."""
        row = self._db.fetch_one("SELECT COUNT(*) AS n FROM appointments WHERE room_id = %s", (room_id,))
        return bool(row and row["n"])


class SettingsRepository(BaseRepository):
    """Key/value clinic settings."""

    table = "clinic_settings"
    columns = ("setting_key", "setting_value", "description", "updated_by")

    def all_rows(self) -> list[Row]:
        return self._db.fetch_all("SELECT setting_key, setting_value, description, updated_at FROM clinic_settings ORDER BY setting_key")

    def as_dict(self) -> dict[str, str]:
        return {r["setting_key"]: r["setting_value"] for r in self.all_rows()}

    def upsert(self, key: str, value: str, user_id: int | None) -> None:
        """Insert or change one setting."""
        self._db.execute(
            "INSERT INTO clinic_settings (setting_key, setting_value, updated_by) VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value), updated_by = VALUES(updated_by)",
            (key, value, user_id),
        )


class AuditRepository(BaseRepository):
    """Append-only activity log."""

    table = "audit_logs"
    columns = ("user_id", "action", "entity", "entity_id", "details")

    def record(self, user_id: int | None, action: str, entity: str | None, entity_id: int | None, details: str | None) -> None:
        """Write one log row. Never pass passwords or medical details."""
        self.create(
            {"user_id": user_id, "action": action, "entity": entity, "entity_id": entity_id, "details": (details or "")[:255] or None}
        )

    def search(self, term: str | None, action: str | None, limit: int, offset: int) -> dict[str, Any]:
        """A page of log rows, the total count, and the list of known actions (for the filter)."""
        conditions, params = ["1 = 1"], []
        if term:
            conditions.append("(a.details LIKE %s OR u.username LIKE %s OR a.entity LIKE %s)")
            params += [f"%{term}%"] * 3
        if action:
            conditions.append("a.action = %s")
            params.append(action)
        where = " AND ".join(conditions)
        total = self._db.fetch_one(
            f"SELECT COUNT(*) AS n FROM audit_logs a LEFT JOIN users u ON u.id = a.user_id WHERE {where}", params
        )
        items = self._db.fetch_all(
            "SELECT a.id, a.user_id, u.username, a.action, a.entity, a.entity_id, a.details, a.created_at "
            f"FROM audit_logs a LEFT JOIN users u ON u.id = a.user_id WHERE {where} "
            "ORDER BY a.created_at DESC, a.id DESC LIMIT %s OFFSET %s",
            [*params, limit, offset],
        )
        actions = [r["action"] for r in self._db.fetch_all("SELECT DISTINCT action FROM audit_logs ORDER BY action")]
        return {"total": int(total["n"]) if total else 0, "items": items, "actions": actions}


class ReportRepository(BaseRepository):
    """Read-only aggregate queries for the admin dashboard and reports."""

    table = "appointments"
    columns = ()

    def overview(self) -> dict[str, Any]:
        """Clinic-wide totals for the admin dashboard."""
        users = {"doctor": 0, "nurse": 0, "admin": 0}
        for r in self._db.fetch_all("SELECT role, COUNT(*) AS n FROM users WHERE is_active = 1 GROUP BY role"):
            users[r["role"]] = int(r["n"])

        def one(sql: str) -> Any:
            row = self._db.fetch_one(sql)
            return row["v"] if row else 0

        return {
            "users": users,
            "patients": int(one("SELECT COUNT(*) AS v FROM patients")),
            "appointments_today": int(one("SELECT COUNT(*) AS v FROM appointments WHERE DATE(scheduled_time) = CURDATE() AND status <> 'Cancelled'")),
            "pending_requests": int(one("SELECT COUNT(*) AS v FROM notifications WHERE status = 'Pending'")),
            "revenue_paid_month": float(one(
                "SELECT COALESCE(SUM(amount), 0) AS v FROM invoices WHERE status = 'Paid' "
                "AND paid_at >= DATE_SUB(CURDATE(), INTERVAL DAYOFMONTH(CURDATE()) - 1 DAY)"
            )),
            "unpaid_total": float(one("SELECT COALESCE(SUM(amount), 0) AS v FROM invoices WHERE status = 'Unpaid'")),
        }

    def report(self, date_from: date, date_to: date) -> dict[str, Any]:
        """Appointments and billing summaries for a date range."""
        rng = (date_from, date_to)
        statuses = self._db.fetch_all(
            "SELECT status, COUNT(*) AS count FROM appointments WHERE DATE(scheduled_time) BETWEEN %s AND %s GROUP BY status", rng
        )
        per_doctor = self._db.fetch_all(
            """
            SELECT u.id AS doctor_id, u.full_name AS doctor_name,
                   COUNT(a.id) AS appointments,
                   COALESCE(SUM(a.status = 'Completed'), 0) AS completed,
                   COALESCE(SUM(a.status = 'Cancelled'), 0) AS cancelled,
                   COALESCE(SUM(CASE WHEN i.status = 'Paid' THEN i.amount END), 0) AS revenue_paid,
                   COALESCE(SUM(CASE WHEN i.status = 'Unpaid' THEN i.amount END), 0) AS revenue_unpaid
            FROM users u
            LEFT JOIN appointments a ON a.doctor_id = u.id AND DATE(a.scheduled_time) BETWEEN %s AND %s
            LEFT JOIN invoices i ON i.appointment_id = a.id
            WHERE u.role = 'doctor' GROUP BY u.id, u.full_name ORDER BY u.full_name
            """,
            rng,
        )
        daily_rows = self._db.fetch_all(
            """
            SELECT DATE(a.scheduled_time) AS report_day, COUNT(a.id) AS appointments,
                   COALESCE(SUM(CASE WHEN i.status = 'Paid' THEN i.amount END), 0) AS revenue
            FROM appointments a LEFT JOIN invoices i ON i.appointment_id = a.id
            WHERE DATE(a.scheduled_time) BETWEEN %s AND %s AND a.status <> 'Cancelled'
            GROUP BY DATE(a.scheduled_time) ORDER BY report_day
            """,
            rng,
        )
        new_patients = self._db.fetch_one("SELECT COUNT(*) AS n FROM patients WHERE DATE(created_at) BETWEEN %s AND %s", rng)
        return {
            "date_from": date_from,
            "date_to": date_to,
            "status_counts": statuses,
            "per_doctor": per_doctor,
            "daily": [{"day": r["report_day"], "appointments": r["appointments"], "revenue": r["revenue"]} for r in daily_rows],
            "totals": {
                "appointments": sum(int(r["count"]) for r in statuses),
                "completed": sum(int(r["count"]) for r in statuses if r["status"] == "Completed"),
                "cancelled": sum(int(r["count"]) for r in statuses if r["status"] == "Cancelled"),
                "revenue_paid": sum(float(r["revenue_paid"]) for r in per_doctor),
                "revenue_unpaid": sum(float(r["revenue_unpaid"]) for r in per_doctor),
                "new_patients": int(new_patients["n"]) if new_patients else 0,
            },
        }