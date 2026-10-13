"""
Business logic for invoices (session billing). The GUI never writes SQL;
it calls this class, which validates the input, talks to the database
through DBConnector, and raises our custom exceptions on problems.

Rules this controller enforces:
  * An invoice is always tied to ONE appointment, and the patient is taken
    from that appointment (so nobody has to type a patient ID).
  * An appointment can only be billed after the doctor has examined the
    patient (status Examined/Completed) - that is also the moment the
    appointment gets its patient_id, which invoices.patient_id requires.
  * An appointment can only have one live (non-cancelled) invoice.
  * Only Unpaid invoices can be marked Paid or Cancelled.

Most methods take `doctor_id`. Pass a doctor's id to limit the result to
that doctor's appointments (Doctor and Nurse screens); pass None to see
every doctor's (Admin screen).
"""

from decimal import Decimal, InvalidOperation

from database.db_connector import DBConnector
from models.invoice import Invoice
from utils.exceptions import EmptyFieldError, InvalidInputError, RecordNotFoundError


class InvoiceController:

    BILLABLE_STATUSES = ("Examined", "Completed")
    MAX_AMOUNT = Decimal("99999999.99")     # invoices.amount is DECIMAL(10,2)

    _SELECT_INVOICES = (
        "SELECT i.*, p.full_name AS patient_name, d.full_name AS doctor_name, "
        "       n.full_name AS issued_by_name "
        "FROM invoices i "
        "JOIN patients p ON i.patient_id = p.id "
        "JOIN appointments a ON i.appointment_id = a.id "
        "JOIN users d ON a.doctor_id = d.id "
        "JOIN users n ON i.issued_by = n.id "
    )

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------
    def get_invoices(self, doctor_id=None, status=None, limit=300):
        """Invoices (newest first) as Invoice objects, optionally limited
        to one doctor's appointments and/or one status."""
        query = self._SELECT_INVOICES
        clauses, params = [], []
        if doctor_id is not None:
            clauses.append("a.doctor_id = %s")
            params.append(doctor_id)
        if status:
            clauses.append("i.status = %s")
            params.append(status)
        if clauses:
            query += "WHERE " + " AND ".join(clauses) + " "
        query += "ORDER BY i.issued_at DESC, i.id DESC LIMIT %s"
        params.append(limit)

        with DBConnector() as db:
            db.execute(query, tuple(params))
            rows = db.fetchall()

        return [
            Invoice(
                invoice_id=row["id"],
                patient_id=row["patient_id"],
                appointment_id=row["appointment_id"],
                issued_by=row["issued_by"],
                amount=row["amount"],
                status=row["status"],
                issued_at=row["issued_at"],
                paid_at=row["paid_at"],
                patient_name=row["patient_name"],
                doctor_name=row["doctor_name"],
                issued_by_name=row["issued_by_name"],
            )
            for row in rows
        ]

    def get_billable_appointments(self, doctor_id=None, limit=200):
        """Appointments that are ready to be billed: the patient has been
        examined (so there IS a patient record) and there is no live
        invoice for them yet. Feeds the dropdown in the Issue Invoice form."""
        query = (
            "SELECT a.id, a.scheduled_time, a.status, p.full_name AS patient_name, "
            "       d.full_name AS doctor_name "
            "FROM appointments a "
            "JOIN patients p ON a.patient_id = p.id "
            "JOIN users d ON a.doctor_id = d.id "
            "WHERE a.patient_id IS NOT NULL "
            "AND a.status IN ('Examined', 'Completed') "
            "AND NOT EXISTS (SELECT 1 FROM invoices i "
            "                WHERE i.appointment_id = a.id AND i.status <> 'Cancelled') "
        )
        params = []
        if doctor_id is not None:
            query += "AND a.doctor_id = %s "
            params.append(doctor_id)
        query += "ORDER BY a.scheduled_time DESC LIMIT %s"
        params.append(limit)

        with DBConnector() as db:
            db.execute(query, tuple(params))
            return db.fetchall()

    def get_summary(self, doctor_id=None):
        """Totals for the cards at the top of the Invoice page:
        {"unpaid_total", "paid_total", "unpaid_count"}. Cancelled
        invoices are ignored."""
        query = (
            "SELECT COALESCE(SUM(CASE WHEN i.status = 'Unpaid' THEN i.amount END), 0) AS unpaid_total, "
            "       COALESCE(SUM(CASE WHEN i.status = 'Paid' THEN i.amount END), 0) AS paid_total, "
            "       COALESCE(SUM(i.status = 'Unpaid'), 0) AS unpaid_count "
            "FROM invoices i JOIN appointments a ON i.appointment_id = a.id "
        )
        params = ()
        if doctor_id is not None:
            query += "WHERE a.doctor_id = %s"
            params = (doctor_id,)

        with DBConnector() as db:
            db.execute(query, params)
            row = db.fetchone() or {}
        return {
            "unpaid_total": row.get("unpaid_total") or Decimal("0"),
            "paid_total": row.get("paid_total") or Decimal("0"),
            "unpaid_count": int(row.get("unpaid_count") or 0),
        }

    # ------------------------------------------------------------------
    # Writing
    # ------------------------------------------------------------------
    def create_invoice(self, appointment_id, issued_by, amount):
        """Issues an Unpaid invoice for one appointment. Returns the new
        invoice id."""
        if not appointment_id:
            raise EmptyFieldError("Choose an appointment to bill.")
        parsed_amount = self._parse_amount(amount)

        with DBConnector() as db:
            db.execute(
                "SELECT id, patient_id, status FROM appointments WHERE id=%s",
                (appointment_id,),
            )
            appt = db.fetchone()
            if appt is None:
                raise RecordNotFoundError("No appointment with id " + str(appointment_id) + ".")
            if appt["patient_id"] is None or appt["status"] not in self.BILLABLE_STATUSES:
                raise InvalidInputError(
                    "This appointment can't be billed yet. The doctor has to examine "
                    "the patient first."
                )

            db.execute(
                "SELECT id FROM invoices WHERE appointment_id=%s AND status <> 'Cancelled'",
                (appointment_id,),
            )
            if db.fetchone() is not None:
                raise InvalidInputError("This appointment already has an invoice.")

            db.execute(
                "INSERT INTO invoices (patient_id, appointment_id, issued_by, amount, status) "
                "VALUES (%s, %s, %s, %s, 'Unpaid')",
                (appt["patient_id"], appointment_id, issued_by, parsed_amount),
            )
            return db.lastrowid

    def mark_paid(self, invoice_id):
        self._change_status(invoice_id, "Paid", "paid")

    def cancel_invoice(self, invoice_id):
        self._change_status(invoice_id, "Cancelled", "cancelled")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _change_status(self, invoice_id, new_status, verb):
        with DBConnector() as db:
            db.execute("SELECT status FROM invoices WHERE id=%s", (invoice_id,))
            row = db.fetchone()
            if row is None:
                raise RecordNotFoundError("No invoice with id " + str(invoice_id) + ".")
            if row["status"] != "Unpaid":
                raise InvalidInputError(
                    "Only unpaid invoices can be " + verb + ". This one is already "
                    + row["status"].lower() + "."
                )
            if new_status == "Paid":
                db.execute(
                    "UPDATE invoices SET status='Paid', paid_at=NOW() WHERE id=%s",
                    (invoice_id,),
                )
            else:
                db.execute(
                    "UPDATE invoices SET status=%s WHERE id=%s",
                    (new_status, invoice_id),
                )

    def _parse_amount(self, amount):
        text = str(amount if amount is not None else "").strip().replace(",", "")
        text = text.lstrip("₱$").strip()
        if text == "":
            raise EmptyFieldError("Invoice amount is required.")
        try:
            value = Decimal(text)
        except InvalidOperation:
            raise InvalidInputError("Invoice amount must be a number, like 500 or 1250.50.")
        if not value.is_finite():
            raise InvalidInputError("Invoice amount must be a number, like 500 or 1250.50.")
        if value > self.MAX_AMOUNT:
            raise InvalidInputError("Invoice amount is too large.")
        value = value.quantize(Decimal("0.01"))     # 2 decimal places, like the database
        if value <= 0:
            raise InvalidInputError("Invoice amount must be greater than zero.")
        return value
