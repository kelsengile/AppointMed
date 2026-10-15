"""
Business logic for managing user accounts (Doctors, Nurses, Admins).
Used by the Admin dashboard and by every role's "My Account" page.
"""

import re

import bcrypt
from mysql.connector import Error as MySQLError
from database.db_connector import DBConnector
from utils.exceptions import (
    RecordNotFoundError,
    EmptyFieldError,
    InvalidCredentialsError,
    PasswordMismatchError,
    UsernameTakenError,
    InvalidInputError,
    DatabaseConnectionError,
)

# Usernames: at least 3 characters, only letters, numbers, dots, underscores.
USERNAME_MIN_LENGTH = 3
USERNAME_PATTERN = re.compile(r"[A-Za-z0-9_.]+")

PASSWORD_MIN_LENGTH = 6


class UserController:

    def get_all_users(self):
        with DBConnector() as db:
            db.execute(
                "SELECT id, username, full_name, role, specialization, assigned_doctor_id "
                "FROM users ORDER BY role, full_name"
            )
            return db.fetchall()

    def get_user_by_id(self, user_id):
        # The profile picture (avatar) is deliberately NOT selected here:
        # it is a large binary column, fetched on its own by get_avatar().
        with DBConnector() as db:
            db.execute(
                "SELECT id, username, full_name, role, specialization, assigned_doctor_id, "
                "created_at FROM users WHERE id=%s",
                (user_id,),
            )
            row = db.fetchone()
            if not row:
                raise RecordNotFoundError("No user with id " + str(user_id) + ".")
            return row

    def get_user_by_username(self, username):
        """Looks up an account by its username instead of its numeric id.

        Used by the Admin "Add User" form so a nurse can be assigned to a
        doctor by typing the doctor's username (e.g. "jdiaz") instead of
        having to know their internal id number, and by anything else
        that wants to show a doctor's name rather than a bare id."""
        username = (username or "").strip()
        if not username:
            raise EmptyFieldError("Username is required.")

        with DBConnector() as db:
            db.execute(
                "SELECT id, username, full_name, role, specialization, assigned_doctor_id "
                "FROM users WHERE username=%s",
                (username,),
            )
            row = db.fetchone()
            if not row:
                raise RecordNotFoundError("No user found with username " + username + ".")
            return row

    def add_user(self, username, password, full_name, role,
                 specialization=None, assigned_doctor_id=None):
        if not username or not password or not full_name:
            raise EmptyFieldError("Username, password, and full name are required.")

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        with DBConnector() as db:
            db.execute(
                "INSERT INTO users (username, password_hash, full_name, role, "
                "specialization, assigned_doctor_id) VALUES (%s, %s, %s, %s, %s, %s)",
                (username, password_hash, full_name, role, specialization, assigned_doctor_id),
            )
            return db.lastrowid

    def delete_user(self, user_id):
        """Deletes an account, first tidying up every row in other tables
        that still points at it. Without this MySQL refuses the delete
        with a foreign key error, because a user's id is referenced by
        appointments, notifications, patients, rooms, examinations,
        prescriptions, invoices and by nurses assigned to a doctor.

        What happens to those rows:
          * appointments the user booked as a nurse   -> kept, nurse cleared
          * appointments belonging to a deleted doctor -> deleted, together
            with their examinations / prescriptions / invoices
          * notifications addressed to the user        -> deleted
          * nurses assigned to the deleted doctor      -> kept, left with no
            assigned doctor
          * patients' primary doctor, room "updated by" -> cleared

        An account that has ISSUED invoices is refused instead, because an
        invoice must always name who issued it.

        Everything runs in ONE transaction: it is committed only at the
        very end, so if any step fails nothing is changed."""
        with DBConnector() as db:
            def run(sql, params=()):
                # Straight to the cursor (not db.execute) so nothing is
                # committed until the final db.commit() below.
                try:
                    db.cursor.execute(sql, params)
                except MySQLError as e:
                    raise DatabaseConnectionError("Could not delete user: " + str(e))

            def ids(sql, params=()):
                run(sql, params)
                return [row["id"] for row in db.cursor.fetchall()]

            def marks(values):
                # "%s, %s, %s" for an IN (...) list; "NULL" when the list
                # is empty, so the IN simply matches nothing.
                return ", ".join(["%s"] * len(values)) or "NULL"

            if not ids("SELECT id FROM users WHERE id=%s", (user_id,)):
                raise RecordNotFoundError("No user with id " + str(user_id) + ".")

            if ids("SELECT id FROM invoices WHERE issued_by=%s LIMIT 1", (user_id,)):
                raise InvalidInputError(
                    "This account has issued invoices and cannot be deleted."
                )

            # ---- a doctor's own records ---------------------------------
            appts = tuple(ids("SELECT id FROM appointments WHERE doctor_id=%s", (user_id,)))
            exams = tuple(ids(
                "SELECT id FROM examinations WHERE doctor_id=%s "
                "OR appointment_id IN (" + marks(appts) + ")",
                (user_id,) + appts
            ))
            prescs = tuple(ids(
                "SELECT id FROM prescriptions WHERE doctor_id=%s "
                "OR examination_id IN (" + marks(exams) + ")",
                (user_id,) + exams
            ))

            run("DELETE FROM prescription_items WHERE prescription_id IN ("
                + marks(prescs) + ")", prescs)
            run("DELETE FROM prescriptions WHERE id IN (" + marks(prescs) + ")", prescs)
            # Another examination may name one of these appointments as its
            # follow-up; unlink it rather than delete that examination.
            run("UPDATE examinations SET follow_up_appointment_id=NULL "
                "WHERE follow_up_appointment_id IN (" + marks(appts) + ")", appts)
            run("DELETE FROM examinations WHERE id IN (" + marks(exams) + ")", exams)
            run("DELETE FROM invoices WHERE appointment_id IN (" + marks(appts) + ")", appts)
            run("DELETE FROM appointments WHERE id IN (" + marks(appts) + ")", appts)

            # ---- notifications addressed to this doctor or nurse ---------
            run("UPDATE appointments SET notification_id=NULL WHERE notification_id IN "
                "(SELECT id FROM notifications WHERE doctor_id=%s OR nurse_id=%s)",
                (user_id, user_id))
            run("DELETE FROM notifications WHERE doctor_id=%s OR nurse_id=%s",
                (user_id, user_id))

            # ---- everything else that merely mentions the user -----------
            run("UPDATE appointments SET nurse_id=NULL WHERE nurse_id=%s", (user_id,))
            run("UPDATE patients SET doctor_id=NULL WHERE doctor_id=%s", (user_id,))
            # updated_at=updated_at stops MySQL stamping a new time on it.
            run("UPDATE rooms SET updated_by=NULL, updated_at=updated_at "
                "WHERE updated_by=%s", (user_id,))
            run("UPDATE users SET assigned_doctor_id=NULL WHERE assigned_doctor_id=%s",
                (user_id,))

            # ---- finally the account itself -----------------------------
            run("DELETE FROM users WHERE id=%s", (user_id,))
            if db.cursor.rowcount == 0:
                raise RecordNotFoundError("No user with id " + str(user_id) + ".")

            db.commit()

    # ------------------------------------------------------------------
    # PROFILE PAGE SUPPORT
    # Used by every role's "My Account" screen (Admin, Doctor, Nurse) so
    # a logged-in user can update their own details instead of an admin
    # having to delete and re-add their account.
    # ------------------------------------------------------------------

    def update_profile(self, user_id, username, full_name, specialization=None):
        """Updates a user's own username, full name and, for doctors,
        specialization, in one go. Returns the cleaned-up values that were
        saved, as a dict, so the screen can show exactly what is stored.

        `specialization` is only touched when a value (including an empty
        string, which clears it to NULL) is explicitly passed in - nurses
        and admins call this with the default None so that column is left
        alone."""
        username = (username or "").strip()
        full_name = (full_name or "").strip()

        if not full_name:
            raise EmptyFieldError("Full name is required.")
        if not username:
            raise EmptyFieldError("Username is required.")
        if len(username) < USERNAME_MIN_LENGTH or not USERNAME_PATTERN.fullmatch(username):
            raise InvalidInputError(
                "Username must be at least " + str(USERNAME_MIN_LENGTH) +
                " characters and use only letters, numbers, dots or underscores."
            )

        with DBConnector() as db:
            # Someone else already using it? (Their own current username
            # is fine - that just means "unchanged".)
            db.execute(
                "SELECT id FROM users WHERE username=%s AND id != %s",
                (username, user_id),
            )
            if db.fetchone():
                raise UsernameTakenError("That username is already taken.")

            saved = {"username": username, "full_name": full_name}
            if specialization is not None:
                saved["specialization"] = specialization.strip() or None
                db.execute(
                    "UPDATE users SET username=%s, full_name=%s, specialization=%s WHERE id=%s",
                    (username, full_name, saved["specialization"], user_id),
                )
            else:
                db.execute(
                    "UPDATE users SET username=%s, full_name=%s WHERE id=%s",
                    (username, full_name, user_id),
                )
            return saved

    def update_details(self, user_id, full_name, specialization=None):
        """Older, name-only version of update_profile(); kept so nothing
        that still calls it breaks."""
        if not full_name or not full_name.strip():
            raise EmptyFieldError("Full name is required.")

        with DBConnector() as db:
            if specialization is not None:
                db.execute(
                    "UPDATE users SET full_name=%s, specialization=%s WHERE id=%s",
                    (full_name.strip(), specialization.strip() or None, user_id),
                )
            else:
                db.execute(
                    "UPDATE users SET full_name=%s WHERE id=%s",
                    (full_name.strip(), user_id),
                )

    def change_password(self, user_id, current_password, new_password, confirm_password):
        """Verifies the account's current password before setting a new
        one, so a logged-in session alone isn't enough to change it -
        the user has to prove they still know the old password."""
        if not current_password or not new_password or not confirm_password:
            raise EmptyFieldError("All password fields are required.")

        if new_password != confirm_password:
            raise PasswordMismatchError("New password and confirmation do not match.")

        if len(new_password) < PASSWORD_MIN_LENGTH:
            raise EmptyFieldError(
                "New password must be at least " + str(PASSWORD_MIN_LENGTH) + " characters long."
            )

        with DBConnector() as db:
            db.execute("SELECT password_hash FROM users WHERE id=%s", (user_id,))
            row = db.fetchone()
            if not row:
                raise RecordNotFoundError("No user with id " + str(user_id) + ".")

            if not bcrypt.checkpw(current_password.encode(), row["password_hash"].encode()):
                raise InvalidCredentialsError("Current password is incorrect.")

            if current_password == new_password:
                raise InvalidInputError("New password must be different from the current one.")

            new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            db.execute("UPDATE users SET password_hash=%s WHERE id=%s", (new_hash, user_id))

    # ------------------------------------------------------------------
    # PROFILE PICTURES
    # The picture lives in the database (users.avatar), so it follows the
    # person to every computer they log in from. utils/avatar.py shrinks
    # it to a small square JPEG before it gets here.
    # ------------------------------------------------------------------

    def get_avatar(self, user_id):
        """The user's stored picture as bytes, or None if they have none."""
        with DBConnector() as db:
            db.execute("SELECT avatar FROM users WHERE id=%s", (user_id,))
            row = db.fetchone()
            if not row or not row["avatar"]:
                return None
            return bytes(row["avatar"])

    def set_avatar(self, user_id, image_bytes):
        with DBConnector() as db:
            db.execute("UPDATE users SET avatar=%s WHERE id=%s", (image_bytes, user_id))

    def remove_avatar(self, user_id):
        with DBConnector() as db:
            db.execute("UPDATE users SET avatar=NULL WHERE id=%s", (user_id,))