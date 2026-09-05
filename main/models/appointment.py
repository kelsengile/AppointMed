"""
Appointment and Patient data models.
Kept as plain, focused classes (models should not know about Tkinter or SQL).
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Patient:
    patient_id: int
    full_name: str
    birthdate: str
    contact_number: str
    address: str = ""


@dataclass
class Appointment:
    appointment_id: int
    patient: Patient
    doctor_id: int
    scheduled_time: datetime
    reason: str
    status: str = "Scheduled"

    def mark_completed(self):
        self.status = "Completed"

    def cancel(self):
        self.status = "Cancelled"

    def is_upcoming(self) -> bool:
        return self.scheduled_time > datetime.now() and self.status == "Scheduled"
