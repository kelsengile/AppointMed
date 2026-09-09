"""
Business logic for appointments. The GUI (views) calls into this class
instead of writing SQL directly. This is the "Controller" part of MVC,
and it is where we check for problems and raise our custom exceptions.
"""

from database.db_connector import DBConnector
from utils.exceptions import DoubleBookingError, InvalidAppointmentTimeError, RecordNotFoundError
from datetime import datetime


class AppointmentController:

    def add_appointment(self, patient_id, doctor_id, scheduled_time, reason):
        if scheduled_time < datetime.now():
            raise InvalidAppointmentTimeError("Cannot schedule an appointment in the past.")

        with DBConnector() as db:
            db.execute(
                "SELECT id FROM appointments WHERE doctor_id=%s AND scheduled_time=%s "
                "AND status != 'Cancelled'",
                (doctor_id, scheduled_time),
            )
            existing = db.fetchone()
            if existing:
                raise DoubleBookingError("This doctor already has an appointment at that time.")

            db.execute(
                "INSERT INTO appointments (patient_id, doctor_id, scheduled_time, reason, status) "
                "VALUES (%s, %s, %s, %s, 'Scheduled')",
                (patient_id, doctor_id, scheduled_time, reason),
            )
            return db.cursor.lastrowid

    def get_schedule_for_doctor(self, doctor_id, date):
        with DBConnector() as db:
            db.execute(
                "SELECT * FROM appointments WHERE doctor_id=%s AND DATE(scheduled_time)=%s "
                "ORDER BY scheduled_time",
                (doctor_id, date),
            )
            return db.fetchall()

    def update_status(self, appointment_id, new_status):
        with DBConnector() as db:
            db.execute(
                "UPDATE appointments SET status=%s WHERE id=%s",
                (new_status, appointment_id),
            )
            if db.cursor.rowcount == 0:
                raise RecordNotFoundError("No appointment with id " + str(appointment_id) + ".")

    def delete_appointment(self, appointment_id):
        with DBConnector() as db:
            db.execute("DELETE FROM appointments WHERE id=%s", (appointment_id,))
            if db.cursor.rowcount == 0:
                raise RecordNotFoundError("No appointment with id " + str(appointment_id) + ".")
