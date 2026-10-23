"""Appointment workflow: check-in, examination, invoice, payment, history."""

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from backend.core.database import Session, database
from backend.core.exceptions import ConflictError, NotFoundError
from backend.core.permissions import doctor_scope
from backend.repositories.booking_repository import PatientRepository
from backend.repositories.user_repository import AuditRepository, SettingsRepository, UserRepository
from backend.repositories.visit_repository import (
    AppointmentRepository,
    ExaminationRepository,
    InvoiceRepository,
    PrescriptionRepository,
)
from backend.schemas.clinic import ExaminationFinish


def _money(value) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class VisitService:
    """Business rules for what happens after a booking is approved."""

    # ---------- appointments page ----------

    def board(self, user: dict, day: date) -> list[dict]:
        doctor_id = doctor_scope(user)
        with database.session() as session:
            return AppointmentRepository(session).board(doctor_id, day)

    def check_in(self, appointment_id: int, user: dict) -> dict:
        """Nurse only (enforced by the route): Scheduled -> Checked-in."""
        with database.session() as session:
            appts = AppointmentRepository(session)
            appt = self._owned(appts, appointment_id, user)
            if appt["status"] != "Scheduled":
                raise ConflictError("Only scheduled appointments can be checked in.")
            if appt["scheduled_time"].date() != date.today():
                raise ConflictError("Only today's appointments can be checked in.")
            appts.check_in(appointment_id, datetime.now())
            AuditRepository(session).log(user["id"], "CHECK_IN", "appointments", appointment_id)
        return {"status": "Checked-in"}

    def cancel(self, appointment_id: int, user: dict) -> dict:
        """Nurse only: Scheduled or Checked-in -> Cancelled (frees the slot)."""
        with database.session() as session:
            appts = AppointmentRepository(session)
            appt = self._owned(appts, appointment_id, user)
            if appt["status"] not in ("Scheduled", "Checked-in"):
                raise ConflictError("This appointment can no longer be cancelled.")
            appts.set_status(appointment_id, "Cancelled")
            AuditRepository(session).log(user["id"], "CANCEL_APPOINTMENT", "appointments", appointment_id)
        return {"status": "Cancelled"}

    def start_exam(self, appointment_id: int, user: dict) -> dict:
        """Doctor only: Checked-in -> Consulting. One at a time. Creates the invoice."""
        with database.session() as session:
            UserRepository(session).lock(user["id"])  # serialises "only one at a time"
            appts = AppointmentRepository(session)
            appt = self._owned(appts, appointment_id, user)
            if appt["status"] != "Checked-in":
                raise ConflictError("Only a checked-in patient can be examined.")
            if appts.consulting(user["id"]):
                raise ConflictError("Finish the current examination before starting another.")

            patient_id = appt["patient_id"]
            if patient_id is None:
                patient_id = PatientRepository(session).create(
                    {"full_name": appt["full_name"], "condition_summary": appt["reason"], "doctor_id": user["id"]}
                )
                appts.set_patient(appointment_id, patient_id)

            invoices = InvoiceRepository(session)
            if invoices.get_by_appointment(appointment_id) is None:
                invoices.create(patient_id, appointment_id, user["id"], self._default_fee(session))
            appts.set_status(appointment_id, "Consulting")
            AuditRepository(session).log(user["id"], "START_EXAM", "appointments", appointment_id)
        return {"status": "Consulting"}

    def finish_exam(self, appointment_id: int, user: dict, data: ExaminationFinish) -> dict:
        """Doctor only: Consulting -> Examined. Saves the exam and prescription and totals the invoice."""
        with database.session() as session:
            appts = AppointmentRepository(session)
            appt = self._owned(appts, appointment_id, user)
            if appt["status"] != "Consulting":
                raise ConflictError("This patient is not under examination.")
            patient_id = appt["patient_id"]

            exam_id = ExaminationRepository(session).create(
                appointment_id, patient_id, user["id"], data.diagnosis.strip(), (data.notes or "").strip() or None
            )
            items = [
                {
                    "medicine_name": i.medicine_name.strip(),
                    "dosage": (i.dosage or "").strip() or None,
                    "quantity": i.quantity,
                    "unit_price": _money(i.unit_price),
                    "instructions": (i.instructions or "").strip() or None,
                }
                for i in data.items
            ]
            if items:
                rx = PrescriptionRepository(session)
                rx_id = rx.create(exam_id, patient_id, user["id"], (data.prescription_notes or "").strip() or None)
                rx.add_items(rx_id, items)
            medicines = sum((_money(i["quantity"] * i["unit_price"]) for i in items), Decimal("0.00"))

            invoices = InvoiceRepository(session)
            invoice = invoices.get_by_appointment(appointment_id)
            if invoice is None:
                invoice_id = invoices.create(patient_id, appointment_id, user["id"], self._default_fee(session))
                invoice = invoices.get(invoice_id)
            fee = _money(data.consultation_fee) if data.consultation_fee is not None else _money(invoice["consultation_fee"])
            invoices.update_totals(invoice["id"], fee, medicines)

            PatientRepository(session).set_condition(patient_id, data.diagnosis.strip())
            appts.set_status(appointment_id, "Examined")
            AuditRepository(session).log(user["id"], "FINISH_EXAM", "appointments", appointment_id)
        return {"status": "Examined", "invoice_id": invoice["id"], "amount": fee + medicines}

    # ---------- invoices ----------

    def invoices(self, user: dict, status: str) -> list[dict]:
        doctor_id = doctor_scope(user)
        with database.session() as session:
            invoices = InvoiceRepository(session)
            # Examined sessions that somehow have no invoice yet get one now.
            for row in invoices.examined_without_invoice(doctor_id):
                invoices.create(row["patient_id"], row["id"], user["id"], self._default_fee(session))
            rows = invoices.for_doctor(doctor_id, None if status == "all" else status)
            items = PrescriptionRepository(session).items_for([r["appointment_id"] for r in rows])
            for row in rows:
                row["items"] = items.get(row["appointment_id"], [])
            return rows

    def pay(self, invoice_id: int, user: dict) -> dict:
        """Doctor or nurse: marks the invoice paid and completes the appointment (moves it to history)."""
        with database.session() as session:
            invoices = InvoiceRepository(session)
            invoice = invoices.get(invoice_id, for_update=True)
            if invoice is None or invoice["doctor_id"] != doctor_scope(user):
                raise NotFoundError("Invoice not found.")
            if invoice["status"] == "Paid":
                raise ConflictError("This invoice is already paid.")
            if invoice["status"] == "Cancelled":
                raise ConflictError("This invoice was cancelled.")
            if invoice["appointment_status"] != "Examined":
                raise ConflictError("The examination must be finished before the invoice can be paid.")
            invoices.mark_paid(invoice_id, user["id"], datetime.now())
            AppointmentRepository(session).set_status(invoice["appointment_id"], "Completed")
            AuditRepository(session).log(user["id"], "PAY_INVOICE", "invoices", invoice_id)
        return {"status": "Paid"}

    # ---------- history and patient records ----------

    def history(self, user: dict, search: str | None, patient_id: int | None) -> list[dict]:
        doctor_id = doctor_scope(user)
        with database.session() as session:
            rows = AppointmentRepository(session).history(doctor_id, (search or "").strip() or None, patient_id)
            items = PrescriptionRepository(session).items_for([r["appointment_id"] for r in rows])
            for row in rows:
                row["items"] = items.get(row["appointment_id"], [])
            return rows

    def patients(self, user: dict, search: str) -> list[dict]:
        doctor_id = doctor_scope(user)
        with database.session() as session:
            return PatientRepository(session).search(doctor_id, search.strip())

    # ---------- helpers ----------

    @staticmethod
    def _owned(appts: AppointmentRepository, appointment_id: int, user: dict) -> dict:
        appt = appts.get(appointment_id, for_update=True)
        if appt is None or appt["doctor_id"] != doctor_scope(user):
            raise NotFoundError("Appointment not found.")
        return appt

    @staticmethod
    def _default_fee(session: Session) -> Decimal:
        try:
            return _money(SettingsRepository(session).get("consultation_fee", "0"))
        except InvalidOperation:
            return Decimal("0.00")


visit_service = VisitService()