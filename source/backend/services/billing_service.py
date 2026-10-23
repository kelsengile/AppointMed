"""Invoices, payments, encounter history, and prescriptions."""

from __future__ import annotations

from datetime import date
from typing import Any

from backend.core.database import Database, Row, database
from backend.core.exceptions import ConflictError, NotFoundError, ValidationFailedError
from backend.core.utils import blank_to_none, to_money
from backend.models.domain import AppointmentWorkflow, User
from backend.repositories.appointment_repository import AppointmentRepository
from backend.repositories.clinical_repository import ExaminationRepository, InvoiceRepository, PrescriptionRepository
from backend.repositories.system_repository import AuditRepository, SettingsRepository


class BillingService:
    """Money-related and record-keeping operations for the user's doctor."""

    def __init__(self, db: Database = database) -> None:
        self._db = db

    def invoices(self, user: User, status: str | None) -> list[Row]:
        """Invoices with their medicine lines."""
        if status and status not in ("Unpaid", "Paid", "Cancelled"):
            raise ValidationFailedError("Unknown status filter.")
        rows = InvoiceRepository(self._db).list_for_doctor(user.scope_doctor_id, status)
        items = PrescriptionRepository(self._db).items_for_appointments([r["appointment_id"] for r in rows])
        for row in rows:
            row["items"] = items.get(row["appointment_id"], [])
        return rows

    def unbilled(self, user: User) -> list[Row]:
        """Examined sessions that still need an invoice."""
        return AppointmentRepository(self._db).unbilled(user.scope_doctor_id)

    def bill(self, user: User, appointment_id: int) -> dict[str, Any]:
        """Create the invoice for an examined session that was never billed."""
        doctor_id = user.scope_doctor_id
        with self._db.transaction() as tx:
            appt = AppointmentRepository(tx).get_item(appointment_id)
            if appt is None or appt["doctor_id"] != doctor_id:
                raise NotFoundError("Appointment not found.")
            if appt["status"] != "Examined":
                raise ConflictError("Only examined sessions can be billed.")
            invoices = InvoiceRepository(tx)
            if invoices.get_by_appointment(appointment_id):
                raise ConflictError("This session already has an invoice.")
            if not appt["patient_id"]:
                raise ConflictError("This session has no patient record yet.")
            lines = PrescriptionRepository(tx).items_for_appointments([appointment_id]).get(appointment_id, [])
            medicines = sum((to_money(l["unit_price"]) * l["quantity"] for l in lines), to_money(0))
            fee = to_money(SettingsRepository(tx).as_dict().get("consultation_fee", "0"))
            new_id = invoices.create(
                {
                    "patient_id": appt["patient_id"], "appointment_id": appointment_id, "issued_by": user.id,
                    "consultation_fee": fee, "medicines_total": medicines, "amount": fee + medicines, "status": "Unpaid",
                }
            )
            AuditRepository(tx).record(user.id, "CREATE_INVOICE", "invoices", new_id, f"Billed appointment #{appointment_id}")
        return {"id": new_id}

    def pay(self, user: User, invoice_id: int) -> None:
        """Record payment. The examination must be finished; paying completes the appointment."""
        doctor_id = user.scope_doctor_id
        with self._db.transaction() as tx:
            invoices = InvoiceRepository(tx)
            invoice = invoices.get_item(invoice_id)
            if invoice is None or invoice["doctor_id"] != doctor_id:
                raise NotFoundError("Invoice not found.")
            if invoice["status"] != "Unpaid":
                raise ConflictError(f"This invoice is already {invoice['status'].lower()}.")
            if invoice["appointment_status"] != "Examined":
                raise ConflictError("The invoice can be paid once the examination is finished.")
            AppointmentWorkflow.ensure(invoice["appointment_status"], "Completed")
            if invoices.mark_paid(invoice_id, user.id) == 0:
                raise ConflictError("This invoice is no longer unpaid.")
            AppointmentRepository(tx).update(invoice["appointment_id"], {"status": "Completed"})
            AuditRepository(tx).record(user.id, "PAY_INVOICE", "invoices", invoice_id, f"Payment received: {invoice['amount']}")

    def history(
        self, user: User, term: str | None, patient_id: int | None, date_from: date | None, date_to: date | None
    ) -> list[Row]:
        """Completed encounters with their medicine lines."""
        if date_from and date_to and date_from > date_to:
            raise ValidationFailedError("The start date must be before the end date.")
        rows = ExaminationRepository(self._db).encounters(user.scope_doctor_id, blank_to_none(term), patient_id, date_from, date_to)
        items = PrescriptionRepository(self._db).items_for_appointments([r["appointment_id"] for r in rows])
        for row in rows:
            row["items"] = items.get(row["appointment_id"], [])
        return rows

    def prescriptions(self, user: User, term: str | None) -> list[Row]:
        return PrescriptionRepository(self._db).list_for_doctor(user.scope_doctor_id, blank_to_none(term))