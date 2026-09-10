"""
Business logic for managing user accounts (Doctors, Nurses, Admins).
Used by the Admin dashboard.
"""

import bcrypt
from database.db_connector import DBConnector
from utils.exceptions import RecordNotFoundError, EmptyFieldError


class UserController:

    def get_all_users(self):
        with DBConnector() as db:
            db.execute(
                "SELECT id, username, full_name, role, specialization, assigned_doctor_id "
                "FROM users ORDER BY role, full_name"
            )
            return db.fetchall()

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
