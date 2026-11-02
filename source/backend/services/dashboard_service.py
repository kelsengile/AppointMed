"""Dashboard summaries for staff and admin, and the admin reports."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from backend.core.database import Database, database
from backend.core.exceptions import ValidationFailedError
from backend.models.domain import AppointmentWorkflow, User
from backend.repositories.appointment_repository import AppointmentRepository, NotificationRepository
from backend.repositories.clinical_repository import InvoiceRepository
from backend.repositories.system_repository import AuditRepository, ReportRepository

from .waiting_queue import WaitingQueue


class DashboardService:
    """Builds the numbers shown on the dashboards."""

    def __init__(self, db: Database = database) -> None:
        self._db = db

    def staff(self, user: User) -> dict[str, Any]:
        """Doctor/nurse dashboard for the user's doctor."""
        doctor_id = user.scope_doctor_id
        appointments = AppointmentRepository(self._db)
        today = {status: 0 for status in AppointmentWorkflow.STATUSES}
        for row in appointments.status_counts_today(doctor_id):
            today[row["status"]] = int(row["n"])
        queue = WaitingQueue()
        for row in appointments.queue(doctor_id):
            queue.push(row)
        return {
            "today": today,
            "pending_notifications": NotificationRepository(self._db).count_pending(doctor_id),
            "unbilled": len(appointments.unbilled(doctor_id)),
            "awaiting_payment": InvoiceRepository(self._db).count_awaiting_payment(doctor_id),
            "queue": queue.ordered(),
            "consulting": appointments.consulting(doctor_id),
            "upcoming": appointments.list_for_doctor(doctor_id, "upcoming", statuses=["Scheduled"])[:5],
        }

    def admin(self) -> dict[str, Any]:
        """Clinic-wide totals plus the latest activity."""
        data = ReportRepository(self._db).overview()
        data["recent_activity"] = AuditRepository(self._db).search(None, None, 8, 0)["items"]
        return data

    def report(self, date_from: date | None, date_to: date | None) -> dict[str, Any]:
        """Appointments and billing summaries (default: the last 30 days)."""
        end = date_to or self._db.server_now().date()
        start = date_from or end - timedelta(days=29)
        if start > end:
            raise ValidationFailedError("The start date must be before the end date.")
        if (end - start).days > 366:
            raise ValidationFailedError("Choose a range of one year or less.")
        return ReportRepository(self._db).report(start, end)