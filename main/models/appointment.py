"""
Simple data classes for Patient and Appointment. These just hold data -
they don't know anything about Tkinter (the GUI) or SQL (the database).
"""

from datetime import datetime


class Patient:
    def __init__(self, patient_id, full_name, birthdate, contact_number, address=""):
        self.patient_id = patient_id
        self.full_name = full_name
        self.birthdate = birthdate
        self.contact_number = contact_number
        self.address = address


class Appointment:
    def __init__(self, appointment_id, patient, doctor_id, scheduled_time, reason, status="Scheduled"):
        self.appointment_id = appointment_id
        self.patient = patient
        self.doctor_id = doctor_id
        self.scheduled_time = scheduled_time
        self.reason = reason
        self.status = status

    def mark_completed(self):
        self.status = "Completed"

    def cancel(self):
        self.status = "Cancelled"

    def is_upcoming(self):
        if self.scheduled_time > datetime.now() and self.status == "Scheduled":
            return True
        return False
