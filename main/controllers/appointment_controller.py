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
    ConsultationInProgressError,
)
from datetime import date, datetime
import calendar


class AppointmentController:

    # The order an appointment naturally moves through, from booking to
    # close-out. next_status() below uses this to figure out what a
    # dashboard's "advance" button should switch an appointment to next.
    # "Consulting" is the patient being with the doctor right now: it is
    # what the queue's Consulting button switches a Checked-in patient to.
    STATUS_FLOW = ["Scheduled", "Checked-in", "Consulting", "Examined", "Completed"]

    def add_appointment(self, full_name, doctor_id, scheduled_time, reason,
                         nurse_id=None, patient_id=None, room_id=None, source="Walk-in",
                         notification_id=None):
        """Books a new appointment. `nurse_id` is the nurse who booked it,
        or None when a doctor books one for themselves. `full_name` is the appointee's name -
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

    def get_month_for_doctor(self, doctor_id, year, month):
        """Appointments for one doctor in one calendar month that are
        still waiting to be checked in (status 'Scheduled'), oldest first.

        Every other status has its own home:
          * Checked-in  -> the waiting queue (get_checkin_queue)
          * Consulting  -> the Consulting section (get_consulting_for_doctor)
          * Completed / Cancelled -> the History page (get_history_for_doctor)
        so none of them appear in this list.

        The month is matched with a >= / < range on scheduled_time rather
        than MONTH()/YEAR(), so the database can use its index."""
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        # Half-open range [first of this month, first of next month).
        next_month_start = date.fromordinal(last_day.toordinal() + 1)

        with DBConnector() as db:
            db.execute(
                "SELECT * FROM appointments WHERE doctor_id=%s "
                "AND scheduled_time >= %s AND scheduled_time < %s "
                "AND status = 'Scheduled' "
                "ORDER BY scheduled_time, id",
                (doctor_id, first_day, next_month_start),
            )
            return db.fetchall()

    def get_checkin_queue(self, doctor_id):
        """The patients who have checked in and are waiting to be seen,
        in the order they should be served: first in, first served, so
        whoever checked in EARLIEST comes first.

        Not limited to any month - it is the live waiting room. Rows that
        were checked in before checked_in_at existed have no timestamp,
        so they fall back to their booked time (and then id) to keep the
        order stable."""
        with DBConnector() as db:
            db.execute(
                "SELECT * FROM appointments WHERE doctor_id=%s AND status='Checked-in' "
                "ORDER BY COALESCE(checked_in_at, scheduled_time), id",
                (doctor_id,),
            )
            return db.fetchall()

    def get_consulting_for_doctor(self, doctor_id):
        """The patient currently being consulted. update_status() only
        allows one at a time per doctor, so this is normally 0 or 1 rows."""
        with DBConnector() as db:
            db.execute(
                "SELECT * FROM appointments WHERE doctor_id=%s AND status='Consulting' "
                "ORDER BY id",
                (doctor_id,),
            )
            return db.fetchall()

    def get_history_for_doctor(self, doctor_id, limit=200):
        """Every finished appointment (Completed OR Cancelled) for one
        doctor, most recent first. This is the History page's data: an
        appointment that is completed or cancelled drops out of every
        other list and shows up here."""
        with DBConnector() as db:
            db.execute(
                "SELECT * FROM appointments WHERE doctor_id=%s "
                "AND status IN ('Completed', 'Cancelled') "
                "ORDER BY scheduled_time DESC, id DESC LIMIT %s",
                (doctor_id, limit),
            )
            return db.fetchall()

    def get_all_appointments(self, limit=200):
        """Every appointment in the system, newest first, with the
        doctor's and nurse's names joined in. Used by the Admin
        dashboard, which oversees every doctor's schedule rather than
        just one."""
        with DBConnector() as db:
            db.execute(
                "SELECT a.*, d.full_name AS doctor_name, "
                "COALESCE(n.full_name, 'none (doctor booked)') AS nurse_name "
                "FROM appointments a "
                "JOIN users d ON a.doctor_id = d.id "
                "LEFT JOIN users n ON a.nurse_id = n.id "
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
            if new_status == "Consulting":
                # Only one patient can be consulted at a time per doctor.
                # The current one has to be finished first.
                db.execute("SELECT doctor_id FROM appointments WHERE id=%s", (appointment_id,))
                appt = db.fetchone()
                if appt is None:
                    raise RecordNotFoundError("No appointment with id " + str(appointment_id) + ".")
                db.execute(
                    "SELECT id FROM appointments "
                    "WHERE doctor_id=%s AND status='Consulting' AND id != %s",
                    (appt["doctor_id"], appointment_id),
                )
                if db.fetchone():
                    raise ConsultationInProgressError(
                        "Another patient is still being consulted. "
                        "Finish that appointment first."
                    )

            if new_status == "Checked-in":
                # Stamp the moment of check-in using the database's own
                # clock (not this machine's), so a nurse's and a doctor's
                # computers can never disagree about who arrived first.
                db.execute(
                    "UPDATE appointments SET status=%s, checked_in_at=NOW() WHERE id=%s",
                    (new_status, appointment_id),
                )
            else:
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