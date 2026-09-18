"""
Business logic for managing user accounts (Doctors, Nurses, Admins).
Used by the Admin dashboard.
"""

import bcrypt
from database.db_connector import DBConnector
from utils.exceptions import (
    RecordNotFoundError,
    EmptyFieldError,
    InvalidCredentialsError,
    PasswordMismatchError,
)


class UserController:

    def get_all_users(self):
        with DBConnector() as db:
            db.execute(
                "SELECT id, username, full_name, role, specialization, assigned_doctor_id "
                "FROM users ORDER BY role, full_name"
            )
            return db.fetchall()

    def get_user_by_id(self, user_id):
        with DBConnector() as db:
            db.execute(
                "SELECT id, username, full_name, role, specialization, assigned_doctor_id "
                "FROM users WHERE id=%s",
                (user_id,),
            )
            row = db.fetchone()
            if not row:
                raise RecordNotFoundError("No user with id " + str(user_id) + ".")
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
        with DBConnector() as db:
            db.execute("DELETE FROM users WHERE id=%s", (user_id,))
            if db.rowcount == 0:
                raise RecordNotFoundError("No user with id " + str(user_id) + ".")

    # ------------------------------------------------------------------
    # PROFILE PAGE SUPPORT
    # Used by every role's "My Account" screen (Admin, Doctor, Nurse) so
    # a logged-in user can update their own details instead of an admin
    # having to delete and re-add their account.
    # ------------------------------------------------------------------

    def update_details(self, user_id, full_name, specialization=None):
        """Updates a user's own full name and, for doctors, specialization.
        `specialization` is only touched when a value (including an empty
        string, which clears it to NULL) is explicitly passed in - nurses
        and admins call this with the default None so that column is left
        alone."""
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

        if len(new_password) < 6:
            raise EmptyFieldError("New password must be at least 6 characters long.")

        with DBConnector() as db:
            db.execute("SELECT password_hash FROM users WHERE id=%s", (user_id,))
            row = db.fetchone()
            if not row:
                raise RecordNotFoundError("No user with id " + str(user_id) + ".")

            if not bcrypt.checkpw(current_password.encode(), row["password_hash"].encode()):
                raise InvalidCredentialsError("Current password is incorrect.")

            new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            db.execute("UPDATE users SET password_hash=%s WHERE id=%s", (new_hash, user_id))
