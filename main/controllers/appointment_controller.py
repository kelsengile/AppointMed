"""
Business logic for appointments. The GUI (views) calls into this class
instead of writing SQL directly. This is the "Controller" part of MVC,
and it is where we check for problems and raise our custom exceptions.
"""

from database.db_connector import DBConnector
from utils.exceptions import (
    DoubleBookingError,
    InvalidAppointmentTimeError,
    RecordNotFoundError,
    EmptyFieldError,
)
from datetime import date, datetime


class AppointmentController:

    # The order an appointment naturally moves through, from booking to
    # close-out. next_status() below uses this to figure out what a
    # dashboard's "advance" button should switch an appointment to next.
    STATUS_FLOW = ["Scheduled", "Checked-in", "Examined", "Completed"]

    def add_appointment(self, full_name, doctor_id, nurse_id, scheduled_time, reason,
                         patient_id=None, room_id=None, source="Walk-in",
                         notification_id=None):
        """Books a new appointment. `full_name` is the appointee's name -
        it's collected up front (by a nurse, from a notification or a
        walk-in) before there is necessarily a patient record yet, which
        is why `patient_id` is optional here and only gets filled in once
        a doctor's examination formally creates/links the patient."""
        if not full_name or not full_name.strip():
            raise EmptyFieldError("Patient/appointee name is required.")

        if not reason or not reason.strip():
            raise EmptyFieldError("Reason for the visit is required.")

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
                "INSERT INTO appointments "
                "(notification_id, patient_id, full_name, doctor_id, nurse_id, room_id, "
                " source, scheduled_time, reason, status) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Scheduled')",
                (notification_id, patient_id, full_name.strip(), doctor_id, nurse_id,
                 room_id, source, scheduled_time, reason.strip()),
            )
            return db.lastrowid

    def get_schedule_for_doctor(self, doctor_id, date):
        """Every appointment for one doctor on one calendar day. Used by
        the Nurse dashboard for their assigned doctor's day. The Doctor
        dashboard uses get_upcoming_for_doctor() below instead, so a visit
        a nurse booked for a later date isn't hidden from them."""
        with DBConnector() as db:
            db.execute(
                "SELECT * FROM appointments WHERE doctor_id=%s AND DATE(scheduled_time)=%s "
                "ORDER BY scheduled_time",
                (doctor_id, date),
            )
            return db.fetchall()

    def get_upcoming_for_doctor(self, doctor_id, from_date=None):
        """Every appointment for one doctor from `from_date` onward
        (defaults to today), oldest first.

        get_schedule_for_doctor() above only ever returns a single day,
        which quietly hides work: a nurse booking a slot for tomorrow -
        which is the normal case, since add_appointment() refuses times
        already in the past - would never show up on the doctor's screen.
        This is the query the Doctor dashboard uses so nothing a nurse
        books can go unseen."""
        if from_date is None:
            from_date = date.today().isoformat()

        with DBConnector() as db:
            db.execute(
                "SELECT * FROM appointments WHERE doctor_id=%s AND DATE(scheduled_time)>=%s "
                "ORDER BY scheduled_time",
                (doctor_id, from_date),
            )
            return db.fetchall()

    def get_all_appointments(self, limit=200):
        """Every appointment in the system, newest first, with the
        doctor's and nurse's names joined in. Used by the Admin
        dashboard, which oversees every doctor's schedule rather than
        just one."""
        with DBConnector() as db:
            db.execute(
                "SELECT a.*, d.full_name AS doctor_name, n.full_name AS nurse_name "
                "FROM appointments a "
                "JOIN users d ON a.doctor_id = d.id "
                "JOIN users n ON a.nurse_id = n.id "
                "ORDER BY a.scheduled_time DESC "
                "LIMIT %s",
                (limit,),
            )
            return db.fetchall()

    def next_status(self, current_status):
        """What an appointment's status should become after one more
        'advance' click, or None if it's already at the end of the flow
        (Completed) or was Cancelled outside the normal flow entirely."""
        if current_status not in self.STATUS_FLOW:
            return None
        index = self.STATUS_FLOW.index(current_status)
        if index + 1 >= len(self.STATUS_FLOW):
            return None
        return self.STATUS_FLOW[index + 1]

    def update_status(self, appointment_id, new_status):
        with DBConnector() as db:
            db.execute(
                "UPDATE appointments SET status=%s WHERE id=%s",
                (new_status, appointment_id),
            )
            if db.rowcount == 0:
                raise RecordNotFoundError("No appointment with id " + str(appointment_id) + ".")

    def delete_appointment(self, appointment_id):
        with DBConnector() as db:
            db.execute("DELETE FROM appointments WHERE id=%s", (appointment_id,))
            if db.rowcount == 0:
                raise RecordNotFoundError("No appointment with id " + str(appointment_id) + ".")
