class Invoice:
    def __init__(self, invoice_id, patient_id, appointment_id, issued_by, amount,
                 status="Unpaid", issued_at=None, paid_at=None,
                 patient_name=None, doctor_name=None, issued_by_name=None):
        self.invoice_id = invoice_id
        self.patient_id = patient_id
        self.appointment_id = appointment_id
        self.issued_by = issued_by
        self.amount = amount
        self.status = status
        self.issued_at = issued_at
        self.paid_at = paid_at
        self.patient_name = patient_name
        self.doctor_name = doctor_name
        self.issued_by_name = issued_by_name

    def is_unpaid(self):
        return self.status == "Unpaid"

    def mark_paid(self):
        self.status = "Paid"

    def cancel(self):
        self.status = "Cancelled"

    def __repr__(self):
        return "<Invoice #" + str(self.invoice_id) + " " + self.status + ">"