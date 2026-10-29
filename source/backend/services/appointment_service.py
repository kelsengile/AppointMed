"""Booking requests and the appointment workflow:
approve/dismiss -> check in -> start exam -> finish exam -> (billing service) pay."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from backend.core.database import Database, Executor, Row, database
from backend.core.exceptions import (
    AppointmentConflictError,
    ConflictError,
    DuplicateEntryError,
    InvalidScheduleError,
    NotFoundError,
    ValidationFailedError,
)
from backend.core.mailer import Mailer, mailer
from backend.core.utils import blank_to_none, floor_minute, to_money, trim
from backend.models.domain import AppointmentWorkflow, User
from backend.repositories.appointment_repository import AppointmentRepository, NotificationRepository
from backend.repositories.clinical_repository import ExaminationRepository, InvoiceRepository, PrescriptionRepository
from backend.repositories.patient_repository import PatientRepository
from backend.repositories.system_repository import AuditRepository, RoomRepository, SettingsRepository
from backend.repositories.user_repository import ScheduleRepository, UserRepository
from backend.schemas.api import AppointmentCreate, ExamFinish

MAX_INVOICE = Decimal("99999999.99")  # fits DECIMAL(10,2)


class AppointmentService:
    """Business rules for notifications and appointments. Works on the user's doctor scope."""

    def __init__(self, db: Database = database, mail: Mailer = mailer) -> None:
        self._db = db
        self._mail = mail

    # ------------------------------------------------------------ helpers
    @staticmethod
    def _load(appointments: AppointmentRepository, doctor_id: int, appointment_id: int) -> Row:
        """Fetch an appointment and make sure it belongs to the user's doctor."""
        row = appointments.get_item(appointment_id)
        if row is None or row["doctor_id"] != doctor_id:
            raise NotFoundError("Appointment not found.")
        return row

    @staticmethod
    def _lock_doctor(tx: Executor, doctor_id: int) -> None:
        """Serialize work for one doctor (for example 'one examination at a time')."""
        tx.fetch_one("SELECT id FROM users WHERE id = %s FOR UPDATE", (doctor_id,))

    @staticmethod
    def _check_room(tx: Executor, room_id: int | None) -> None:
        """A room must exist and not be under maintenance."""
        if room_id is None:
            return
        room = RoomRepository(tx).get(room_id)
        if room is None:
            raise NotFoundError("Room not found.")
        if room["status"] == "Maintenance":
            raise ConflictError("That room is under maintenance.")

    @staticmethod
    def _free_room(tx: Executor, room_id: int | None, user_id: int) -> None:
        """Mark an occupied room as available again."""
        if not room_id:
            return
        room = RoomRepository(tx).get(room_id)
        if room and room["status"] == "Occupied":
            RoomRepository(tx).update(room_id, {"status": "Available", "updated_by": user_id})

    @staticmethod
    def _ensure_patient(tx: Executor, appt: Row) -> int:
        """Make sure the appointment points to a patient record, creating or reusing one."""
        if appt["patient_id"]:
            return appt["patient_id"]
        patients = PatientRepository(tx)
        match = patients.find_match(appt["full_name"], appt.get("birthdate"))
        patient_id = match["id"] if match else patients.create(
            {
                "full_name": appt["full_name"],
                "birthdate": appt.get("birthdate"),
                "sex": appt.get("sex"),
                "contact_number": appt.get("contact_number"),
                "doctor_id": appt["doctor_id"],
            }
        )
        AppointmentRepository(tx).update(appt["id"], {"patient_id": patient_id})
        return patient_id

    @staticmethod
    def _parse_when(day: str) -> str | date:
        if day in ("today", "upcoming", "all"):
            return day
        try:
            return date.fromisoformat(day)
        except ValueError as exc:
            raise ValidationFailedError("Invalid day filter.") from exc

    # ------------------------------------------------------------ notifications
    def list_notifications(self, user: User, status: str | None) -> list[Row]:
        if status and status not in ("Pending", "Converted", "Dismissed"):
            raise ValidationFailedError("Unknown status filter.")
        return NotificationRepository(self._db).list_for_doctor(user.scope_doctor_id, status)

    def approve_notification(self, user: User, notification_id: int, room_id: int | None, scheduled_time: datetime | None) -> Row:
        """Turn a pending request into an appointment (creating or reusing the patient) and email the requester."""
        doctor_id = user.scope_doctor_id
        with self._db.transaction() as tx:
            notifications, appointments = NotificationRepository(tx), AppointmentRepository(tx)
            note = notifications.get(notification_id)
            if note is None or note["doctor_id"] != doctor_id:
                raise NotFoundError("Request not found.")
            if note["status"] != "Pending":
                raise ConflictError("This request was already handled.")
            chosen = scheduled_time or note["preferred_datetime"]
            if chosen is None:
                raise ValidationFailedError("Choose a date and time for this appointment.")
            when = floor_minute(chosen)
            if when < floor_minute(tx.server_now()):
                raise InvalidScheduleError("That time has already passed. Choose a later time.")
            self._check_room(tx, room_id)
            if appointments.conflict_exists(doctor_id, when):
                raise AppointmentConflictError()

            patients = PatientRepository(tx)
            patient = patients.find_match(note["requester_name"], note["birthdate"])
            if patient:
                patient_id = patient["id"]
                contact = {k: note[k] for k in ("contact_number", "email", "address") if note[k]}
                if contact:
                    patients.update(patient_id, contact)
            else:
                patient_id = patients.create(
                    {
                        "full_name": note["requester_name"], "birthdate": note["birthdate"], "sex": note["sex"],
                        "contact_number": note["contact_number"], "email": note["email"], "address": note["address"],
                        "doctor_id": doctor_id,
                    }
                )
            try:
                new_id = appointments.create(
                    {
                        "notification_id": notification_id, "patient_id": patient_id, "full_name": note["requester_name"],
                        "doctor_id": doctor_id, "nurse_id": user.id if user.role == "nurse" else note["nurse_id"],
                        "room_id": room_id, "source": "Notification", "scheduled_time": when, "reason": note["reason"],
                        "status": "Scheduled",
                    }
                )
            except DuplicateEntryError as exc:
                raise AppointmentConflictError() from exc
            # The conditional update decides a race between two people approving at once: the loser rolls back.
            if notifications.resolve(notification_id, "Converted", None, user.id) == 0:
                raise ConflictError("This request was already handled.")
            AuditRepository(tx).record(user.id, "APPROVE_REQUEST", "notifications", notification_id, f"Created appointment #{new_id}")
            clinic = SettingsRepository(tx).as_dict().get("clinic_name", "the clinic")
            doctor_name = UserRepository(tx).get(doctor_id)["full_name"]  # type: ignore[index]
        self._mail.send(
            note["email"],
            f"Your appointment at {clinic} is confirmed",
            f"Hello {note['requester_name']},\n\nYour appointment with {doctor_name} is confirmed for "
            f"{when:%A, %B %d, %Y at %I:%M %p}.\nPlease arrive a few minutes early.\n\n{clinic}",
        )
        return AppointmentRepository(self._db).get_item(new_id)  # type: ignore[return-value]

    def dismiss_notification(self, user: User, notification_id: int, note_text: str) -> None:
        """Dismiss a pending request and email the reason."""
        doctor_id = user.scope_doctor_id
        with self._db.transaction() as tx:
            notifications = NotificationRepository(tx)
            note = notifications.get(notification_id)
            if note is None or note["doctor_id"] != doctor_id:
                raise NotFoundError("Request not found.")
            if notifications.resolve(notification_id, "Dismissed", note_text, user.id) == 0:
                raise ConflictError("This request was already handled.")
            AuditRepository(tx).record(user.id, "DISMISS_REQUEST", "notifications", notification_id, trim(note_text, 200))
            clinic = SettingsRepository(tx).as_dict().get("clinic_name", "the clinic")
        self._mail.send(
            note["email"],
            f"About your appointment request at {clinic}",
            f"Hello {note['requester_name']},\n\nWe could not confirm your appointment request.\nReason: {note_text}\n\n"
            f"Please request another time or call the clinic.\n\n{clinic}",
        )

    # ------------------------------------------------------------ appointments
    def list_appointments(self, user: User, day: str, term: str | None) -> list[Row]:
        return AppointmentRepository(self._db).list_for_doctor(user.scope_doctor_id, self._parse_when(day), blank_to_none(term))

    def calendar(self, user: User, start: date, end: date) -> dict[str, Any]:
        """Which weekdays the doctor works, and which days already have bookings (for the agenda calendar)."""
        if start > end or (end - start).days > 62:
            raise ValidationFailedError("Choose a range of two months or less.")
        doctor_id = user.scope_doctor_id
        blocks = ScheduleRepository(self._db).blocks_for_doctor(doctor_id)
        busy = AppointmentRepository(self._db).booked_days(doctor_id, start, end) | NotificationRepository(
            self._db
        ).pending_days(doctor_id, start, end)
        return {
            "working_weekdays": sorted({b["weekday"] for b in blocks}),
            "busy_days": sorted(d.isoformat() for d in busy),
        }

    def create_appointment(self, user: User, data: AppointmentCreate) -> Row:
        """Create a walk-in or phone appointment for the user's doctor."""
        doctor_id = user.scope_doctor_id
        with self._db.transaction() as tx:
            patients, appointments = PatientRepository(tx), AppointmentRepository(tx)
            if data.patient_id:
                patient = patients.get_scoped(data.patient_id, doctor_id)
                if patient is None:
                    raise NotFoundError("Patient not found.")
                patient_id, name = patient["id"], patient["full_name"]
            else:
                name = blank_to_none(data.full_name)  # type: ignore[assignment]
                if not name:
                    raise ValidationFailedError("Enter the patient's name or choose an existing patient.")
                match = patients.find_match(name, data.birthdate)
                patient_id = match["id"] if match else patients.create(
                    {
                        "full_name": name, "birthdate": data.birthdate, "sex": data.sex,
                        "contact_number": blank_to_none(data.contact_number), "doctor_id": doctor_id,
                    }
                )
            now = tx.server_now()
            when = floor_minute(data.scheduled_time or now)
            if when.date() < now.date():
                raise InvalidScheduleError("Choose today or a later date.")
            if data.check_in_now and when.date() != now.date():
                raise ValidationFailedError("Only today's appointments can be checked in.")
            if appointments.conflict_exists(doctor_id, when):
                raise AppointmentConflictError()
            try:
                new_id = appointments.create(
                    {
                        "patient_id": patient_id, "full_name": name, "doctor_id": doctor_id,
                        "nurse_id": user.id if user.role == "nurse" else None, "source": "Walk-in",
                        "scheduled_time": when, "reason": blank_to_none(data.reason),
                        "status": "Checked-in" if data.check_in_now else "Scheduled",
                        "checked_in_at": now if data.check_in_now else None,
                    }
                )
            except DuplicateEntryError as exc:
                raise AppointmentConflictError() from exc
            AuditRepository(tx).record(user.id, "CREATE_APPOINTMENT", "appointments", new_id, f"Walk-in for {trim(name, 60)}")
        return AppointmentRepository(self._db).get_item(new_id)  # type: ignore[return-value]

    def check_in(self, user: User, appointment_id: int) -> Row:
        """Move a scheduled appointment into the waiting queue. A room must be chosen first."""
        doctor_id = user.scope_doctor_id
        with self._db.transaction() as tx:
            appointments = AppointmentRepository(tx)
            appt = self._load(appointments, doctor_id, appointment_id)
            AppointmentWorkflow.ensure(appt["status"], "Checked-in")
            if not appt["room_id"]:
                raise ValidationFailedError("Choose an exam room before checking the patient in.")
            now = tx.server_now()
            if appt["scheduled_time"].date() > now.date():
                raise ValidationFailedError("Only today's appointments can be checked in.")
            self._ensure_patient(tx, appt)
            appointments.update(appointment_id, {"status": "Checked-in", "checked_in_at": now})
            AuditRepository(tx).record(user.id, "CHECK_IN", "appointments", appointment_id, None)
        return AppointmentRepository(self._db).get_item(appointment_id)  # type: ignore[return-value]

    def start_exam(self, user: User, appointment_id: int, room_id: int | None) -> Row:
        """Doctor starts the examination: occupy a room and create the invoice (consultation fee only)."""
        doctor_id = user.scope_doctor_id
        with self._db.transaction() as tx:
            self._lock_doctor(tx, doctor_id)  # two simultaneous starts can no longer both pass the check below
            appointments = AppointmentRepository(tx)
            appt = self._load(appointments, doctor_id, appointment_id)
            AppointmentWorkflow.ensure(appt["status"], "Consulting")
            if appointments.consulting(doctor_id, appointment_id):
                raise ConflictError("Finish the examination that is already in progress first.")
            patient_id = self._ensure_patient(tx, appt)
            chosen_room = room_id or appt["room_id"]
            if chosen_room:
                room = RoomRepository(tx).get(chosen_room)
                if room is None:
                    raise NotFoundError("Room not found.")
                if room["status"] != "Available":
                    raise ConflictError(f"{room['room_name']} is {room['status'].lower()}. Choose another room.")
                RoomRepository(tx).update(chosen_room, {"status": "Occupied", "updated_by": user.id})
            appointments.update(appointment_id, {"status": "Consulting", "room_id": chosen_room})
            invoices = InvoiceRepository(tx)
            if invoices.get_by_appointment(appointment_id) is None:
                fee = to_money(SettingsRepository(tx).as_dict().get("consultation_fee", "0"))
                invoices.create(
                    {
                        "patient_id": patient_id, "appointment_id": appointment_id, "issued_by": user.id,
                        "consultation_fee": fee, "medicines_total": to_money(0), "amount": fee, "status": "Unpaid",
                    }
                )
            AuditRepository(tx).record(user.id, "START_EXAM", "appointments", appointment_id, None)
        return AppointmentRepository(self._db).get_item(appointment_id)  # type: ignore[return-value]

    def release(self, user: User, appointment_id: int) -> Row:
        """Send a patient back to the queue (examination started by mistake)."""
        doctor_id = user.scope_doctor_id
        with self._db.transaction() as tx:
            appointments = AppointmentRepository(tx)
            appt = self._load(appointments, doctor_id, appointment_id)
            AppointmentWorkflow.ensure(appt["status"], "Checked-in")
            self._free_room(tx, appt["room_id"], user.id)
            appointments.update(appointment_id, {"status": "Checked-in"})
            AuditRepository(tx).record(user.id, "RETURN_TO_QUEUE", "appointments", appointment_id, None)
        return AppointmentRepository(self._db).get_item(appointment_id)  # type: ignore[return-value]

    def finish_exam(self, user: User, appointment_id: int, data: ExamFinish) -> Row:
        """Save the examination, prescription and invoice totals; optionally book a follow-up."""
        doctor_id = user.scope_doctor_id
        items = [
            {
                "medicine_name": i.medicine_name, "dosage": blank_to_none(i.dosage), "quantity": i.quantity,
                "unit_price": to_money(i.unit_price), "instructions": blank_to_none(i.instructions),
            }
            for i in data.items
        ]
        medicines = sum((i["unit_price"] * i["quantity"] for i in items), to_money(0))
        fee = to_money(data.consultation_fee)
        if fee + medicines > MAX_INVOICE:
            raise ValidationFailedError("The invoice total is too large. Check the quantities and prices.")

        with self._db.transaction() as tx:
            appointments = AppointmentRepository(tx)
            appt = self._load(appointments, doctor_id, appointment_id)
            AppointmentWorkflow.ensure(appt["status"], "Examined")
            patient_id = self._ensure_patient(tx, appt)
            now = tx.server_now()

            follow_up_id: int | None = None
            if data.follow_up_time:
                when = floor_minute(data.follow_up_time)
                if when <= now:
                    raise InvalidScheduleError("The follow-up must be in the future.")
                if appointments.conflict_exists(doctor_id, when):
                    raise AppointmentConflictError("The follow-up time is already booked.")
                nurses = UserRepository(tx).nurses_for_doctor(doctor_id)
                try:
                    follow_up_id = appointments.create(
                        {
                            "patient_id": patient_id, "full_name": appt["full_name"], "doctor_id": doctor_id,
                            "nurse_id": nurses[0]["id"] if nurses else None, "source": "Follow-up", "scheduled_time": when,
                            "reason": trim(f"Follow-up: {appt['reason'] or 'checkup'}", 255), "status": "Scheduled",
                        }
                    )
                except DuplicateEntryError as exc:
                    raise AppointmentConflictError("The follow-up time is already booked.") from exc

            exam_id = ExaminationRepository(tx).create(
                {
                    "appointment_id": appointment_id, "patient_id": patient_id, "doctor_id": doctor_id,
                    "diagnosis": data.diagnosis, "notes": blank_to_none(data.notes),
                    "outcome": "Follow-up Scheduled" if follow_up_id else "Sent to History",
                    "follow_up_appointment_id": follow_up_id,
                }
            )
            # Keep the short "latest condition" on the patient record in step with the newest diagnosis.
            PatientRepository(tx).update(patient_id, {"condition_summary": trim(" ".join(data.diagnosis.split()), 255)})

            if items or blank_to_none(data.prescription_notes):
                prescriptions = PrescriptionRepository(tx)
                rx_id = prescriptions.create(
                    {
                        "examination_id": exam_id, "patient_id": patient_id, "doctor_id": doctor_id,
                        "notes": blank_to_none(data.prescription_notes),
                    }
                )
                prescriptions.add_items(rx_id, items)

            invoices = InvoiceRepository(tx)
            invoice = invoices.get_by_appointment(appointment_id)
            if invoice is None:
                invoices.create(
                    {
                        "patient_id": patient_id, "appointment_id": appointment_id, "issued_by": user.id,
                        "consultation_fee": fee, "medicines_total": medicines, "amount": fee + medicines, "status": "Unpaid",
                    }
                )
            else:
                invoices.set_amounts(invoice["id"], fee, medicines)

            self._free_room(tx, appt["room_id"], user.id)
            appointments.update(appointment_id, {"status": "Examined"})
            AuditRepository(tx).record(user.id, "FINISH_EXAM", "appointments", appointment_id, None)
        return AppointmentRepository(self._db).get_item(appointment_id)  # type: ignore[return-value]

    def cancel(self, user: User, appointment_id: int, reason: str | None) -> Row:
        """Cancel a scheduled or checked-in appointment (frees the slot for rebooking)."""
        doctor_id = user.scope_doctor_id
        with self._db.transaction() as tx:
            appointments = AppointmentRepository(tx)
            appt = self._load(appointments, doctor_id, appointment_id)
            AppointmentWorkflow.ensure(appt["status"], "Cancelled")
            appointments.update(appointment_id, {"status": "Cancelled"})
            invoice = InvoiceRepository(tx).get_by_appointment(appointment_id)
            if invoice and invoice["status"] == "Unpaid":
                InvoiceRepository(tx).update(invoice["id"], {"status": "Cancelled"})
            AuditRepository(tx).record(user.id, "CANCEL_APPOINTMENT", "appointments", appointment_id, trim(reason or "No reason given", 200))
        return AppointmentRepository(self._db).get_item(appointment_id)  # type: ignore[return-value]

    def reschedule(self, user: User, appointment_id: int, new_time: datetime) -> Row:
        """Move a scheduled appointment to another time."""
        doctor_id = user.scope_doctor_id
        with self._db.transaction() as tx:
            appointments = AppointmentRepository(tx)
            appt = self._load(appointments, doctor_id, appointment_id)
            if appt["status"] != "Scheduled":
                raise ConflictError("Only scheduled appointments can be rescheduled.")
            when = floor_minute(new_time)
            if when <= tx.server_now():
                raise InvalidScheduleError("Choose a time in the future.")
            if appointments.conflict_exists(doctor_id, when, appointment_id):
                raise AppointmentConflictError()
            try:
                appointments.update(appointment_id, {"scheduled_time": when})
            except DuplicateEntryError as exc:
                raise AppointmentConflictError() from exc
            AuditRepository(tx).record(user.id, "RESCHEDULE_APPOINTMENT", "appointments", appointment_id, f"Moved to {when:%Y-%m-%d %H:%M}")
        return AppointmentRepository(self._db).get_item(appointment_id)  # type: ignore[return-value]

    def assign_room(self, user: User, appointment_id: int, room_id: int | None) -> Row:
        """Pick (or clear) the exam room for an appointment that has not started."""
        doctor_id = user.scope_doctor_id
        with self._db.transaction() as tx:
            appointments = AppointmentRepository(tx)
            appt = self._load(appointments, doctor_id, appointment_id)
            if appt["status"] not in ("Scheduled", "Checked-in"):
                raise ConflictError("A room can only be chosen before the examination starts.")
            self._check_room(tx, room_id)
            appointments.update(appointment_id, {"room_id": room_id})
        return AppointmentRepository(self._db).get_item(appointment_id)  # type: ignore[return-value]

    # ------------------------------------------------------------ rooms
    def list_rooms(self) -> list[Row]:
        return RoomRepository(self._db).list_with_occupant()

    def set_room_status(self, user: User, room_id: int, status: str) -> None:
        """Nurses and doctors can flip a room between Available, Occupied and Maintenance."""
        with self._db.transaction() as tx:
            rooms = RoomRepository(tx)
            if rooms.get(room_id) is None:
                raise NotFoundError("Room not found.")
            rooms.update(room_id, {"status": status, "updated_by": user.id})
            AuditRepository(tx).record(user.id, "UPDATE_ROOM_STATUS", "rooms", room_id, f"Status set to {status}")