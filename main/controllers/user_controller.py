"""
Business logic for managing user accounts (Doctors, Nurses, Admins).
Used by the Admin dashboard and by every role's "My Account" page.
"""

import re

import bcrypt
from database.db_connector import DBConnector
from utils.exceptions import (
    RecordNotFoundError,
    EmptyFieldError,
    InvalidCredentialsError,
    PasswordMismatchError,
    UsernameTakenError,
    InvalidInputError,
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