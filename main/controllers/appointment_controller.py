"""
Business logic for appointments — the GUI layer calls into this instead
of writing SQL directly. This is the "Controller" in MVC and is where
validation + custom exceptions get raised.
"""

from database.db_connector import DBConnector
from utils.exceptions import DoubleBookingError, InvalidAppointmentTimeError, RecordNotFoundError
from datetime import datetime


class AppointmentController:

    def add_appointment(self, patient_id: int, doctor_id: int,
                         scheduled_time: datetime, reason: str) -> int:
        if scheduled_time < datetime.now():
            raise InvalidAppointmentTimeError("Cannot schedule an appointment in the past.")

        with DBConnector() as db:
            db.execute(
                "SELECT id FROM appointments WHERE doctor_id=%s AND scheduled_time=%s "
                "AND status != 'Cancelled'",
                (doctor_id, scheduled_time),
            )
            if db.fetchone():
                raise DoubleBookingError("This doctor already has an appointment at that time.")

            db.execute(
                "INSERT INTO appointments (patient_id, doctor_id, scheduled_time, reason, status) "
                "VALUES (%s, %s, %s, %s, 'Scheduled')",
                (patient_id, doctor_id, scheduled_time, reason),
            )
            return db._cursor.lastrowid

    def get_schedule_for_doctor(self, doctor_id: int, date: str) -> list[dict]:
        with DBConnector() as db:
            db.execute(
                "SELECT * FROM appointments WHERE doctor_id=%s AND DATE(scheduled_time)=%s "
                "ORDER BY scheduled_time",
                (doctor_id, date),
            )
            return db.fetchall()

    def update_status(self, appointment_id: int, new_status: str):
        with DBConnector() as db:
            db.execute(
                "UPDATE appointments SET status=%s WHERE id=%s",
                (new_status, appointment_id),
            )
            if db._cursor.rowcount == 0:
                raise RecordNotFoundError(f"No appointment with id {appointment_id}.")

    def delete_appointment(self, appointment_id: int):
        with DBConnector() as db:
            db.execute("DELETE FROM appointments WHERE id=%s", (appointment_id,))
            if db._cursor.rowcount == 0:
                raise RecordNotFoundError(f"No appointment with id {appointment_id}.")
