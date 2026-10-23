"""The public booking page: catalog, open slots, and request submission."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from backend.core.database import Database, database
from backend.core.exceptions import AppError, InvalidScheduleError, NotFoundError, ValidationFailedError
from backend.core.utils import floor_minute
from backend.repositories.appointment_repository import NotificationRepository
from backend.repositories.system_repository import AuditRepository, SettingsRepository
from backend.repositories.user_repository import UserRepository
from backend.schemas.api import BookingRequest

from .scheduling_service import SchedulingService


class BookingService:
    """Everything a patient can do without an account."""

    def __init__(self, db: Database = database) -> None:
        self._db = db

    def _settings(self) -> dict[str, str]:
        return SettingsRepository(self._db).as_dict()

    @staticmethod
    def _is_open(settings: dict[str, str]) -> bool:
        return settings.get("online_booking_enabled", "true").lower() == "true"

    @staticmethod
    def _window(settings: dict[str, str]) -> int:
        try:
            return int(settings.get("booking_window_days", "30"))
        except ValueError:
            return 30

    def catalog(self) -> dict[str, Any]:
        """Clinic info and the doctors that can be booked."""
        settings = self._settings()
        return {
            "clinic_name": settings.get("clinic_name", "AppointMed"),
            "clinic_address": settings.get("clinic_address", ""),
            "booking_open": self._is_open(settings),
            "window_days": self._window(settings),
            "doctors": UserRepository(self._db).public_doctors(),
        }

    def _ensure_day_allowed(self, day: date, settings: dict[str, str]) -> None:
        if not self._is_open(settings):
            raise AppError("Online booking is currently closed. Please call the clinic.")
        today = self._db.server_now().date()
        if day < today or day > today + timedelta(days=self._window(settings)):
            raise InvalidScheduleError("Choose a date within the booking window.")

    def slots(self, doctor_id: int, day: date) -> dict[str, list[str]]:
        """Open times for a doctor on a day, as ISO strings."""
        self._ensure_day_allowed(day, self._settings())
        found = SchedulingService(self._db).available_slots(doctor_id, day)
        return {"slots": [s.isoformat(timespec="seconds") for s in found]}

    def book(self, request: BookingRequest) -> dict[str, Any]:
        """Store a booking request for the doctor and one of their nurses."""
        settings = self._settings()
        when = floor_minute(request.preferred_datetime)
        self._ensure_day_allowed(when.date(), settings)
        with self._db.transaction() as tx:
            doctor = UserRepository(tx).get(request.doctor_id)
            if doctor is None or doctor["role"] != "doctor" or not doctor["is_active"]:
                raise NotFoundError("Doctor not found.")
            SchedulingService(tx).ensure_bookable(request.doctor_id, when)
            nurses = UserRepository(tx).nurses_for_doctor(request.doctor_id)
            if not request.email:
                raise ValidationFailedError("An email address is required.")
            new_id = NotificationRepository(tx).create(
                {
                    "doctor_id": request.doctor_id,
                    "nurse_id": nurses[0]["id"] if nurses else None,
                    "requester_name": request.full_name,
                    "contact_number": request.contact_number,
                    "email": request.email,
                    "birthdate": request.birthdate,
                    "sex": request.sex,
                    "address": request.address,
                    "preferred_datetime": when,
                    "reason": request.reason,
                    "origin": "Website",
                    "status": "Pending",
                }
            )
            AuditRepository(tx).record(None, "BOOKING_REQUEST", "notifications", new_id, "New request from the public website")
        return {
            "id": new_id,
            "doctor_name": doctor["full_name"],
            "preferred_datetime": when.isoformat(timespec="seconds"),
            "email": request.email,
        }