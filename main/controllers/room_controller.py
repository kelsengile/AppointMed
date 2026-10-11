"""
Room data for the clinic. Uses the `rooms` table and the
`appointments.room_id` column that schema.sql already has, so there is
nothing to migrate.

HOW A ROOM'S STATUS IS WORKED OUT
    * "Maintenance" is the only status that is STORED (a nurse or a doctor
      switches it on/off).
    * "Occupied"  is never stored: a room is occupied whenever one of its
      appointments is in "Consulting" right now.
    * Otherwise it is "Available".
Because Occupied is derived from the appointments themselves, the Room page
can never disagree with the Appointments page.

RULES WHEN ASSIGNING A ROOM TO AN APPOINTMENT
    * A room under Maintenance can never be assigned.
    * A room that is Occupied right now CAN be assigned (the booking is for
      a later time slot) ...
    * ... but the same room can never be booked twice for the same time.
"""

from database.db_connector import DBConnector
from utils.exceptions import AppointMedError, DatabaseConnectionError

DEFAULT_ROOMS = ("Room 101", "Room 102", "Room 103", "Room 104")
ACTIVE_STATUSES = "('Scheduled', 'Checked-in', 'Consulting')"


def attach_rooms(controller, *appointment_lists):
    """Adds the room name to the end of each appointment's `reason` text,
    e.g. "Fever   ·   Room 102", so every card that already prints the
    reason shows the room too without any drawing code changing. Safe to
    call when nothing has a room - those cards are left untouched."""
    ids = [a["id"] for appts in appointment_lists for a in appts]
    try:
        names = controller.room_names_for(ids)
    except AppointMedError:
        return
    for appts in appointment_lists:
        for a in appts:
            name = names.get(a["id"])
            if name:
                a["reason"] = a["reason"] + "   ·   " + name


class RoomController:
    def __init__(self):
        self._seeded = False

    # ---------------------------------------------------------------
    # small database helpers
    # ---------------------------------------------------------------
    def _query(self, sql, params=()):
        try:
            with DBConnector() as db:
                db.execute(sql, params)
                return db.fetchall()
        except DatabaseConnectionError as e:
            raise AppointMedError(str(e))

    def _run(self, sql, params=()):
        try:
            with DBConnector() as db:
                db.execute(sql, params)
        except DatabaseConnectionError as e:
            raise AppointMedError(str(e))

    def ensure_default_rooms(self):
        """First run only: the rooms table starts empty, so create a few."""
        if self._seeded:
            return
        rows = self._query("SELECT COUNT(*) AS n FROM rooms")
        if rows[0]["n"] == 0:
            for name in DEFAULT_ROOMS:
                self._run("INSERT INTO rooms (room_name) VALUES (%s)", (name,))
        self._seeded = True

    # ---------------------------------------------------------------
    # reading
    # ---------------------------------------------------------------
    def list_rooms(self):
        """[{id, name, status, patient}] - status is Available / Occupied /
        Maintenance (see the top of this file); `patient` is who is inside
        when Occupied."""
        self.ensure_default_rooms()
        rows = self._query(
            "SELECT r.id, r.room_name, r.status AS stored_status, "
            "(SELECT a.full_name FROM appointments a "
            " WHERE a.room_id = r.id AND a.status = 'Consulting' LIMIT 1) AS current_patient "
            "FROM rooms r ORDER BY r.room_name"
        )
        rooms = []
        for row in rows:
            if row["stored_status"] == "Maintenance":
                status = "Maintenance"
            elif row["current_patient"]:
                status = "Occupied"
            else:
                status = "Available"
            rooms.append({
                "id": row["id"], "name": row["room_name"],
                "status": status, "patient": row["current_patient"],
            })
        return rooms

    def room_names_for(self, appointment_ids):
        """{appointment_id: room_name} for those appointments that have a room."""
        ids = list(appointment_ids)
        if not ids:
            return {}
        placeholders = ", ".join(["%s"] * len(ids))
        rows = self._query(
            "SELECT a.id, r.room_name FROM appointments a "
            "JOIN rooms r ON r.id = a.room_id WHERE a.id IN (" + placeholders + ")",
            tuple(ids)
        )
        return {row["id"]: row["room_name"] for row in rows}

    # ---------------------------------------------------------------
    # assigning rooms
    # ---------------------------------------------------------------
    def validate_room(self, room_id, scheduled_time, ignore_appointment_id=None):
        """Raises AppointMedError if this room can't take an appointment at
        `scheduled_time`. Call it BEFORE booking so nothing half-saves."""
        rows = self._query("SELECT room_name, status FROM rooms WHERE id = %s", (room_id,))
        if not rows:
            raise AppointMedError("That room does not exist.")
        room = rows[0]
        if room["status"] == "Maintenance":
            raise AppointMedError(room["room_name"] + " is under maintenance and cannot be assigned.")

        sql = ("SELECT id FROM appointments WHERE room_id = %s AND scheduled_time = %s "
               "AND status IN " + ACTIVE_STATUSES)
        params = [room_id, scheduled_time]
        if ignore_appointment_id is not None:
            sql += " AND id <> %s"
            params.append(ignore_appointment_id)
        if self._query(sql, tuple(params)):
            raise AppointMedError(room["room_name"] + " is already booked at that time.")

    def assign_room(self, appointment_id, room_id):
        rows = self._query("SELECT scheduled_time FROM appointments WHERE id = %s", (appointment_id,))
        if not rows:
            raise AppointMedError("That appointment no longer exists.")
        self.validate_room(room_id, rows[0]["scheduled_time"], ignore_appointment_id=appointment_id)
        self._run("UPDATE appointments SET room_id = %s WHERE id = %s", (room_id, appointment_id))

    # (A new booking passes room_id straight to add_appointment(); call
    #  validate_room() just before it so a refused room saves nothing.)

    # ---------------------------------------------------------------
    # maintenance (nurse or doctor may toggle it)
    # ---------------------------------------------------------------
    def set_maintenance(self, room_id, on, user_id):
        if on:
            busy = self._query(
                "SELECT id FROM appointments WHERE room_id = %s AND status = 'Consulting'",
                (room_id,)
            )
            if busy:
                raise AppointMedError("A patient is being consulted in this room right now.")
        self._run(
            "UPDATE rooms SET status = %s, updated_by = %s WHERE id = %s",
            ("Maintenance" if on else "Available", user_id, room_id)
        )