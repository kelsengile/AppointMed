"""Computes the open appointment slots for a doctor on a day."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from backend.core.database import Executor
from backend.core.exceptions import InvalidScheduleError, NotFoundError
from backend.repositories.appointment_repository import AppointmentRepository
from backend.repositories.user_repository import ScheduleRepository, UserRepository


class SchedulingService:
    """Turns weekly schedule blocks into bookable slots, removing taken and past times."""

    def __init__(self, db: Executor) -> None:
        self._db = db
        self._users = UserRepository(db)
        self._schedules = ScheduleRepository(db)
        self._appointments = AppointmentRepository(db)

    def available_slots(self, doctor_id: int, day: date) -> list[datetime]:
        """Open slot start times for the doctor on `day`, in order."""
        doctor = self._users.get(doctor_id)
        if doctor is None or doctor["role"] != "doctor" or not doctor["is_active"]:
            raise NotFoundError("Doctor not found.")
        now = self._db.server_now()
        taken = self._appointments.booked_times(doctor_id, day)
        slots: list[datetime] = []
        for block in self._schedules.blocks_for_day(doctor_id, day.isoweekday()):
            cursor = datetime.combine(day, block["start_time"])
            end = datetime.combine(day, block["end_time"])
            step = timedelta(minutes=block["slot_minutes"])
            while cursor + step <= end:
                if cursor > now and cursor not in taken:
                    slots.append(cursor)
                cursor += step
        return sorted(slots)

    def ensure_bookable(self, doctor_id: int, when: datetime) -> None:
        """Raise InvalidScheduleError unless `when` is one of the doctor's open slots."""
        if when not in self.available_slots(doctor_id, when.date()):
            raise InvalidScheduleError("That time is no longer available. Please choose another.")