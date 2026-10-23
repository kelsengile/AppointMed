"""Public booking and the staff decision on each request."""

from datetime import date, datetime, time, timedelta

from backend.core.database import Session, database
from backend.core.exceptions import (
    AppointmentConflictError,
    BookingClosedError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from backend.core.mailer import mailer
from backend.core.permissions import doctor_scope
from backend.repositories.booking_repository import NotificationRepository, PatientRepository
from backend.repositories.user_repository import (
    AuditRepository,
    ScheduleRepository,
    SettingsRepository,
    UserRepository,
    as_delta,
)
from backend.repositories.visit_repository import AppointmentRepository
from backend.schemas.clinic import BookingRequest


def _when(slot: datetime) -> tuple[str, str]:
    return slot.strftime("%A, %B %d, %Y"), slot.strftime("%I:%M %p").lstrip("0")


class BookingService:
    """Computes open slots, stores requests, and approves or dismisses them."""

    # ---------- public side ----------

    def catalog(self) -> dict:
        """Doctors a patient can choose from, with their working weekdays."""
        with database.session() as session:
            cfg = SettingsRepository(session)
            weekdays = ScheduleRepository(session).weekdays_by_doctor()
            doctors = [
                {**doctor, "weekdays": weekdays[doctor["id"]]}
                for doctor in UserRepository(session).bookable_doctors()
                if doctor["id"] in weekdays
            ]
            return {
                "clinic_name": cfg.get("clinic_name", "AppointMed"),
                "booking_open": cfg.get_bool("online_booking_enabled", True),
                "window_days": int(cfg.get("booking_window_days", "30") or 30),
                "doctors": doctors,
            }

    def available_slots(self, doctor_id: int, day: date) -> list[str]:
        with database.session() as session:
            self._assert_open(session)
            self._require_doctor(session, doctor_id)
            return [s.isoformat(timespec="seconds") for s in self._open_slots(session, doctor_id, day)]

    def submit_request(self, data: BookingRequest) -> dict:
        slot = data.preferred_datetime.replace(tzinfo=None, second=0, microsecond=0)
        with database.session() as session:
            self._assert_open(session)
            doctor = self._require_doctor(session, data.doctor_id)
            if slot not in self._open_slots(session, doctor["id"], slot.date()):
                raise ConflictError("That time is no longer available. Please pick another slot.")
            nurse_id = UserRepository(session).nurse_for_doctor(doctor["id"])
            payload = data.model_dump()
            payload["preferred_datetime"] = slot
            notification_id = NotificationRepository(session).create(doctor["id"], nurse_id, payload)
            AuditRepository(session).log(
                None, "BOOKING_REQUEST", "notifications", notification_id, "New request from the public website"
            )
            clinic = SettingsRepository(session).get("clinic_name", "AppointMed")

        day, clock = _when(slot)
        mailer.send(
            data.email,
            f"We received your appointment request - {clinic}",
            f"Hello {data.full_name},\n\n"
            f"We received your request to see {doctor['full_name']} on {day} at {clock}.\n"
            "A member of our staff will review it and email you again once it is confirmed or if the time "
            "cannot be accommodated.\n\nThis request is not a confirmed appointment yet.\n\n"
            f"{clinic}",
        )
        return {
            "id": notification_id,
            "doctor_name": doctor["full_name"],
            "preferred_datetime": slot.isoformat(timespec="seconds"),
            "email": data.email,
        }

    # ---------- staff side ----------

    def list_notifications(self, user: dict, status: str) -> list[dict]:
        doctor_id = doctor_scope(user)
        with database.session() as session:
            return NotificationRepository(session).for_doctor(doctor_id, None if status == "all" else status)

    def approve(self, notification_id: int, user: dict) -> dict:
        with database.session() as session:
            notes = NotificationRepository(session)
            note = self._pending_for(notes, notification_id, user)
            slot = note["preferred_datetime"]
            if slot is None:
                raise ConflictError("This request has no appointment time. Dismiss it and contact the patient.")
            if slot < datetime.now():
                raise ConflictError("The requested time has already passed. Dismiss it and contact the patient.")
            appts = AppointmentRepository(session)
            if appts.slot_taken(note["doctor_id"], slot):
                raise AppointmentConflictError("The doctor already has an appointment at that time.")

            patients = PatientRepository(session)
            patient_id = patients.find_match(note["requester_name"], note["birthdate"])
            if patient_id is None:
                patient_id = patients.create(
                    {
                        "full_name": note["requester_name"],
                        "birthdate": note["birthdate"],
                        "sex": note["sex"],
                        "contact_number": note["contact_number"],
                        "email": note["email"],
                        "address": note["address"],
                        "condition_summary": note["reason"],
                        "doctor_id": note["doctor_id"],
                    }
                )
            else:
                patients.update_contact(patient_id, note["contact_number"], note["email"], note["address"])

            nurse_id = user["id"] if user["role"] == "nurse" else note["nurse_id"]
            appointment_id = appts.create(
                note["id"], patient_id, note["requester_name"], note["doctor_id"], nurse_id,
                "Notification", slot, note["reason"],
            )
            notes.resolve(note["id"], "Converted", user["id"], None)
            AuditRepository(session).log(
                user["id"], "APPROVE_BOOKING", "appointments", appointment_id, f"From request #{note['id']}"
            )
            doctor = UserRepository(session).get(note["doctor_id"])
            clinic = SettingsRepository(session).get("clinic_name", "AppointMed")
            address = SettingsRepository(session).get("clinic_address", "")

        day, clock = _when(slot)
        mailer.send(
            note["email"],
            f"Your appointment is confirmed - {clinic}",
            f"Hello {note['requester_name']},\n\nYour appointment is confirmed.\n\n"
            f"Doctor: {doctor['full_name'] if doctor else ''}\nDate: {day}\nTime: {clock}\n"
            f"Reason: {note['reason'] or '-'}\n\n"
            "Please arrive about 10 minutes early and tell the nurse your name at the front desk."
            + (f"\nClinic address: {address}" if address else "")
            + f"\n\nThank you,\n{clinic}",
        )
        return {"appointment_id": appointment_id, "patient_id": patient_id, "emailed": bool(note["email"])}

    def dismiss(self, notification_id: int, user: dict, reason: str | None) -> dict:
        reason = (reason or "").strip() or None
        with database.session() as session:
            notes = NotificationRepository(session)
            note = self._pending_for(notes, notification_id, user)
            notes.resolve(note["id"], "Dismissed", user["id"], reason)
            AuditRepository(session).log(user["id"], "DISMISS_BOOKING", "notifications", note["id"])
            doctor = UserRepository(session).get(note["doctor_id"])
            clinic = SettingsRepository(session).get("clinic_name", "AppointMed")
            frontend_book = "the booking page on our website"

        slot = note["preferred_datetime"]
        asked = ""
        if slot:
            day, clock = _when(slot)
            asked = f" for {day} at {clock}" + (f" with {doctor['full_name']}" if doctor else "")
        mailer.send(
            note["email"],
            f"Update on your appointment request - {clinic}",
            f"Hello {note['requester_name']},\n\nWe are sorry, but we could not confirm your appointment request{asked}.\n"
            + (f"\nReason: {reason}\n" if reason else "")
            + f"\nYou are welcome to submit a new request using {frontend_book} and choose another time.\n\n"
            f"Thank you,\n{clinic}",
        )
        return {"status": "Dismissed", "emailed": bool(note["email"])}

    # ---------- helpers ----------

    @staticmethod
    def _assert_open(session: Session) -> None:
        if not SettingsRepository(session).get_bool("online_booking_enabled", True):
            raise BookingClosedError("Online booking is currently closed. Please call the clinic.")

    @staticmethod
    def _require_doctor(session: Session, doctor_id: int) -> dict:
        doctor = UserRepository(session).get(doctor_id)
        if doctor is None or doctor["role"] != "doctor" or not doctor["is_active"]:
            raise NotFoundError("That doctor is not available.")
        return doctor

    @staticmethod
    def _pending_for(notes: NotificationRepository, notification_id: int, user: dict) -> dict:
        note = notes.get(notification_id, for_update=True)
        if note is None:
            raise NotFoundError("Request not found.")
        if note["doctor_id"] != doctor_scope(user):
            raise ForbiddenError("This request is not addressed to you.")
        if note["status"] != "Pending":
            raise ConflictError("This request was already handled.")
        return note

    @staticmethod
    def _open_slots(session: Session, doctor_id: int, day: date) -> list[datetime]:
        """Slots from the doctor's weekly schedule that are in the future and not yet taken or requested."""
        now = datetime.now()
        window = int(SettingsRepository(session).get("booking_window_days", "30") or 30)
        if day < now.date() or day > now.date() + timedelta(days=window):
            return []
        day_start = datetime.combine(day, time.min)
        day_end = day_start + timedelta(days=1)
        taken = set(AppointmentRepository(session).taken_slots(doctor_id, day_start, day_end))
        taken |= set(NotificationRepository(session).pending_slots(doctor_id, day_start, day_end))
        slots: list[datetime] = []
        for block in ScheduleRepository(session).blocks_for(doctor_id, day.isoweekday()):
            start = day_start + as_delta(block["start_time"])
            end = day_start + as_delta(block["end_time"])
            step = timedelta(minutes=block["slot_minutes"])
            current = start
            while current + step <= end:
                if current > now and current not in taken:
                    slots.append(current)
                current += step
        return sorted(slots)


booking_service = BookingService()