"""Examinations, prescriptions, and invoices."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any

from backend.core.database import Row

from .base_repository import BaseRepository, placeholders


class ExaminationRepository(BaseRepository):
    """The doctor's record of seeing a patient."""

    table = "examinations"
    columns = ("appointment_id", "patient_id", "doctor_id", "diagnosis", "notes", "outcome", "follow_up_appointment_id")

    def encounters(
        self,
        doctor_id: int,
        term: str | None = None,
        patient_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Row]:
        """Completed encounters (paid sessions), newest first."""
        conditions, params = ["a.doctor_id = %s", "a.status = 'Completed'"], [doctor_id]
        if patient_id:
            conditions.append("a.patient_id = %s")
            params.append(patient_id)
        if term:
            conditions.append("(a.full_name LIKE %s OR ex.diagnosis LIKE %s OR a.reason LIKE %s)")
            params += [f"%{term}%"] * 3
        if date_from:
            conditions.append("DATE(a.scheduled_time) >= %s")
            params.append(date_from)  # type: ignore[arg-type]
        if date_to:
            conditions.append("DATE(a.scheduled_time) <= %s")
            params.append(date_to)  # type: ignore[arg-type]
        return self._db.fetch_all(
            """
            SELECT a.id AS appointment_id, a.patient_id, a.full_name, a.scheduled_time, a.reason,
                   ex.diagnosis, ex.notes, ex.examined_at,
                   i.id AS invoice_id, i.consultation_fee, i.medicines_total, i.amount, i.paid_at
            FROM appointments a
            LEFT JOIN examinations ex ON ex.appointment_id = a.id
            LEFT JOIN invoices i ON i.appointment_id = a.id
            WHERE """
            + " AND ".join(conditions)
            + " ORDER BY a.scheduled_time DESC, a.id DESC LIMIT 500",
            params,
        )


class PrescriptionRepository(BaseRepository):
    """Prescriptions and their medicine lines."""

    table = "prescriptions"
    columns = ("examination_id", "patient_id", "doctor_id", "notes")

    def add_items(self, prescription_id: int, items: list[dict[str, Any]]) -> None:
        """Insert medicine lines for a prescription."""
        for item in items:
            self._db.execute(
                "INSERT INTO prescription_items (prescription_id, medicine_name, dosage, quantity, unit_price, instructions) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (prescription_id, item["medicine_name"], item["dosage"], item["quantity"], item["unit_price"], item["instructions"]),
            )

    def items_for_appointments(self, appointment_ids: list[int]) -> dict[int, list[Row]]:
        """Medicine lines grouped by appointment id."""
        grouped: dict[int, list[Row]] = defaultdict(list)
        if not appointment_ids:
            return grouped
        rows = self._db.fetch_all(
            "SELECT pi.id, pi.medicine_name, pi.dosage, pi.quantity, pi.unit_price, pi.instructions, ex.appointment_id "
            "FROM prescription_items pi JOIN prescriptions rx ON rx.id = pi.prescription_id "
            "JOIN examinations ex ON ex.id = rx.examination_id "
            f"WHERE ex.appointment_id IN ({placeholders(len(appointment_ids))}) ORDER BY pi.id",
            appointment_ids,
        )
        for row in rows:
            grouped[row["appointment_id"]].append(row)
        return grouped

    def list_for_doctor(self, doctor_id: int, term: str | None = None) -> list[Row]:
        """A doctor's prescriptions with their medicine lines."""
        sql = (
            "SELECT rx.id, rx.issued_at, rx.notes, rx.patient_id, p.full_name AS patient_name, "
            "ex.diagnosis, ex.appointment_id FROM prescriptions rx "
            "JOIN examinations ex ON ex.id = rx.examination_id JOIN patients p ON p.id = rx.patient_id "
            "WHERE rx.doctor_id = %s"
        )
        params: list[Any] = [doctor_id]
        if term:
            sql += " AND (p.full_name LIKE %s OR ex.diagnosis LIKE %s)"
            params += [f"%{term}%"] * 2
        rows = self._db.fetch_all(sql + " ORDER BY rx.issued_at DESC, rx.id DESC LIMIT 300", params)
        items: dict[int, list[Row]] = defaultdict(list)
        if rows:
            for item in self._db.fetch_all(
                "SELECT id, prescription_id, medicine_name, dosage, quantity, unit_price, instructions "
                f"FROM prescription_items WHERE prescription_id IN ({placeholders(len(rows))}) ORDER BY id",
                [r["id"] for r in rows],
            ):
                items[item["prescription_id"]].append(item)
        for row in rows:
            row["items"] = items.get(row["id"], [])
        return rows


class InvoiceRepository(BaseRepository):
    """One invoice per appointment."""

    table = "invoices"
    columns = ("patient_id", "appointment_id", "issued_by", "consultation_fee", "medicines_total", "amount", "status", "paid_by")

    def get_by_appointment(self, appointment_id: int) -> Row | None:
        return self._db.fetch_one("SELECT * FROM invoices WHERE appointment_id = %s", (appointment_id,))

    def get_item(self, invoice_id: int) -> Row | None:
        """An invoice with its appointment's doctor and status (used for access checks)."""
        return self._db.fetch_one(
            "SELECT i.*, a.doctor_id, a.status AS appointment_status FROM invoices i "
            "JOIN appointments a ON a.id = i.appointment_id WHERE i.id = %s",
            (invoice_id,),
        )

    def list_for_doctor(self, doctor_id: int, status: str | None = None) -> list[Row]:
        """A doctor's invoices, newest first."""
        sql = (
            "SELECT i.id, i.appointment_id, i.patient_id, p.full_name AS patient_name, a.scheduled_time, "
            "a.status AS appointment_status, i.consultation_fee, i.medicines_total, i.amount, i.status, i.issued_at, i.paid_at "
            "FROM invoices i JOIN appointments a ON a.id = i.appointment_id JOIN patients p ON p.id = i.patient_id "
            "WHERE a.doctor_id = %s"
        )
        params: list[Any] = [doctor_id]
        if status:
            sql += " AND i.status = %s"
            params.append(status)
        return self._db.fetch_all(sql + " ORDER BY i.issued_at DESC, i.id DESC LIMIT 500", params)

    def set_amounts(self, invoice_id: int, fee: Decimal, medicines: Decimal) -> int:
        """Store the consultation fee, medicines total and their sum (unpaid invoices only)."""
        return self._db.update(
            "UPDATE invoices SET consultation_fee = %s, medicines_total = %s, amount = %s WHERE id = %s AND status = 'Unpaid'",
            (fee, medicines, fee + medicines, invoice_id),
        )

    def mark_paid(self, invoice_id: int, user_id: int) -> int:
        """Mark an unpaid invoice as paid now. Returns 0 if it was not unpaid."""
        return self._db.update(
            "UPDATE invoices SET status = 'Paid', paid_at = NOW(), paid_by = %s WHERE id = %s AND status = 'Unpaid'",
            (user_id, invoice_id),
        )

    def count_awaiting_payment(self, doctor_id: int) -> int:
        row = self._db.fetch_one(
            "SELECT COUNT(*) AS n FROM invoices i JOIN appointments a ON a.id = i.appointment_id "
            "WHERE a.doctor_id = %s AND i.status = 'Unpaid' AND a.status = 'Examined'",
            (doctor_id,),
        )
        return int(row["n"]) if row else 0