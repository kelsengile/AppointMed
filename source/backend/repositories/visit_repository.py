"""SQL for appointments, examinations, prescriptions, and invoices."""

from datetime import date, datetime
from decimal import Decimal

from mysql.connector.errors import IntegrityError

from backend.core.database import Session
from backend.core.exceptions import AppointmentConflictError

APPOINTMENT_BOARD_SELECT = """
SELECT a.id, a.notification_id, a.patient_id, a.full_name, a.doctor_id, a.nurse_id, a.source,
       a.scheduled_time, a.reason, a.status, a.checked_in_at,
       p.birthdate, p.sex, p.contact_number, p.email,
       i.id AS invoice_id, i.consultation_fee, i.amount AS invoice_amount, i.status AS invoice_status
FROM appointments a
LEFT JOIN patients p ON p.id = a.patient_id
LEFT JOIN invoices i ON i.appointment_id = a.id
"""

APPOINTMENT_BASIC = (
    "SELECT id, patient_id, full_name, doctor_id, nurse_id, status, scheduled_time, reason FROM appointments"
)


class AppointmentRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def create(
        self,
        notification_id: int | None,
        patient_id: int | None,
        full_name: str,
        doctor_id: int,
        nurse_id: int | None,
        source: str,
        scheduled_time: datetime,
        reason: str | None,
    ) -> int:
        try:
            return self._s.execute(
                "INSERT INTO appointments (notification_id, patient_id, full_name, doctor_id, nurse_id, "
                "source, scheduled_time, reason) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (notification_id, patient_id, full_name, doctor_id, nurse_id, source, scheduled_time, reason),
            )
        except IntegrityError as exc:
            if exc.errno == 1062:
                raise AppointmentConflictError("That time slot was just taken. Please choose another.") from exc
            raise

    def get(self, appointment_id: int, for_update: bool = False) -> dict | None:
        sql = APPOINTMENT_BASIC + " WHERE id = %s" + (" FOR UPDATE" if for_update else "")
        return self._s.one(sql, (appointment_id,))

    def slot_taken(self, doctor_id: int, slot: datetime) -> bool:
        row = self._s.one(
            "SELECT id FROM appointments WHERE doctor_id = %s AND active_slot = %s LIMIT 1", (doctor_id, slot)
        )
        return row is not None

    def taken_slots(self, doctor_id: int, start: datetime, end: datetime) -> list[datetime]:
        rows = self._s.all(
            "SELECT scheduled_time FROM appointments WHERE doctor_id = %s AND status <> 'Cancelled' "
            "AND scheduled_time >= %s AND scheduled_time < %s",
            (doctor_id, start, end),
        )
        return [row["scheduled_time"] for row in rows]

    def board(self, doctor_id: int, day: date) -> list[dict]:
        """Everything the appointments page shows: the queue, the exam room, unpaid sessions, and the day's agenda."""
        return self._s.all(
            APPOINTMENT_BOARD_SELECT
            + " WHERE a.doctor_id = %s AND (a.status IN ('Checked-in', 'Consulting', 'Examined') "
            "OR (a.status = 'Scheduled' AND DATE(a.scheduled_time) = %s)) ORDER BY a.scheduled_time",
            (doctor_id, day),
        )

    def consulting(self, doctor_id: int) -> dict | None:
        return self._s.one(
            "SELECT id FROM appointments WHERE doctor_id = %s AND status = 'Consulting' LIMIT 1", (doctor_id,)
        )

    def set_status(self, appointment_id: int, status: str) -> None:
        self._s.execute("UPDATE appointments SET status = %s WHERE id = %s", (status, appointment_id))

    def check_in(self, appointment_id: int, when: datetime) -> None:
        self._s.execute(
            "UPDATE appointments SET status = 'Checked-in', checked_in_at = %s WHERE id = %s",
            (when, appointment_id),
        )

    def set_patient(self, appointment_id: int, patient_id: int) -> None:
        self._s.execute("UPDATE appointments SET patient_id = %s WHERE id = %s", (patient_id, appointment_id))

    def history(self, doctor_id: int, search: str | None, patient_id: int | None) -> list[dict]:
        sql = (
            "SELECT a.id AS appointment_id, a.patient_id, a.full_name, a.scheduled_time, a.reason, "
            "e.diagnosis, e.notes, e.examined_at, "
            "i.id AS invoice_id, i.consultation_fee, i.medicines_total, i.amount, i.paid_at "
            "FROM appointments a "
            "LEFT JOIN examinations e ON e.appointment_id = a.id "
            "LEFT JOIN invoices i ON i.appointment_id = a.id "
            "WHERE a.doctor_id = %s AND a.status = 'Completed'"
        )
        params: list = [doctor_id]
        if patient_id is not None:
            sql += " AND a.patient_id = %s"
            params.append(patient_id)
        if search:
            sql += " AND a.full_name LIKE %s"
            params.append(f"%{search}%")
        sql += " ORDER BY a.scheduled_time DESC LIMIT 200"
        return self._s.all(sql, params)


class ExaminationRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, appointment_id: int, patient_id: int, doctor_id: int, diagnosis: str, notes: str | None) -> int:
        return self._s.execute(
            "INSERT INTO examinations (appointment_id, patient_id, doctor_id, diagnosis, notes, outcome) "
            "VALUES (%s, %s, %s, %s, %s, 'Sent to History')",
            (appointment_id, patient_id, doctor_id, diagnosis, notes),
        )


class PrescriptionRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, examination_id: int, patient_id: int, doctor_id: int, notes: str | None) -> int:
        return self._s.execute(
            "INSERT INTO prescriptions (examination_id, patient_id, doctor_id, notes) VALUES (%s, %s, %s, %s)",
            (examination_id, patient_id, doctor_id, notes),
        )

    def add_items(self, prescription_id: int, items: list[dict]) -> None:
        for item in items:
            self._s.execute(
                "INSERT INTO prescription_items (prescription_id, medicine_name, dosage, quantity, "
                "unit_price, instructions) VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    prescription_id,
                    item["medicine_name"],
                    item["dosage"],
                    item["quantity"],
                    item["unit_price"],
                    item["instructions"],
                ),
            )

    def items_for(self, appointment_ids: list[int]) -> dict[int, list[dict]]:
        """Prescribed medicines grouped by appointment id."""
        if not appointment_ids:
            return {}
        marks = ",".join(["%s"] * len(appointment_ids))
        rows = self._s.all(
            "SELECT e.appointment_id, pi.id, pi.medicine_name, pi.dosage, pi.quantity, pi.unit_price, "
            "pi.instructions FROM prescription_items pi "
            "JOIN prescriptions pr ON pr.id = pi.prescription_id "
            "JOIN examinations e ON e.id = pr.examination_id "
            f"WHERE e.appointment_id IN ({marks}) ORDER BY pi.id",
            appointment_ids,
        )
        grouped: dict[int, list[dict]] = {}
        for row in rows:
            grouped.setdefault(row.pop("appointment_id"), []).append(row)
        return grouped


# Older sample rows were saved with only `amount`; show that amount as the consultation fee.
_INVOICE_SELECT = """
SELECT i.id, i.appointment_id, i.patient_id,
       IF(i.consultation_fee = 0 AND i.medicines_total = 0, i.amount, i.consultation_fee) AS consultation_fee,
       i.medicines_total, i.amount, i.status, i.issued_at, i.paid_at,
       a.full_name AS patient_name, a.scheduled_time, a.status AS appointment_status, a.doctor_id
FROM invoices i JOIN appointments a ON a.id = i.appointment_id
"""


class InvoiceRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, patient_id: int, appointment_id: int, issued_by: int, fee: Decimal) -> int:
        return self._s.execute(
            "INSERT INTO invoices (patient_id, appointment_id, issued_by, consultation_fee, medicines_total, amount) "
            "VALUES (%s, %s, %s, %s, 0, %s)",
            (patient_id, appointment_id, issued_by, fee, fee),
        )

    def get(self, invoice_id: int, for_update: bool = False) -> dict | None:
        sql = _INVOICE_SELECT + " WHERE i.id = %s" + (" FOR UPDATE" if for_update else "")
        return self._s.one(sql, (invoice_id,))

    def get_by_appointment(self, appointment_id: int) -> dict | None:
        return self._s.one(_INVOICE_SELECT + " WHERE i.appointment_id = %s", (appointment_id,))

    def update_totals(self, invoice_id: int, fee: Decimal, medicines: Decimal) -> None:
        self._s.execute(
            "UPDATE invoices SET consultation_fee = %s, medicines_total = %s, amount = %s WHERE id = %s",
            (fee, medicines, fee + medicines, invoice_id),
        )

    def mark_paid(self, invoice_id: int, user_id: int, when: datetime) -> None:
        self._s.execute(
            "UPDATE invoices SET status = 'Paid', paid_at = %s, paid_by = %s WHERE id = %s",
            (when, user_id, invoice_id),
        )

    def for_doctor(self, doctor_id: int, status: str | None) -> list[dict]:
        sql = _INVOICE_SELECT + " WHERE a.doctor_id = %s"
        params: list = [doctor_id]
        if status:
            sql += " AND i.status = %s"
            params.append(status)
        sql += " ORDER BY (i.status = 'Unpaid') DESC, i.issued_at DESC LIMIT 200"
        return self._s.all(sql, params)

    def examined_without_invoice(self, doctor_id: int) -> list[dict]:
        return self._s.all(
            "SELECT a.id, a.patient_id FROM appointments a LEFT JOIN invoices i ON i.appointment_id = a.id "
            "WHERE a.doctor_id = %s AND a.status = 'Examined' AND a.patient_id IS NOT NULL AND i.id IS NULL",
            (doctor_id,),
        )