"""
Business logic for managing user accounts (Doctors, Nurses, Admins).
Used by the Admin dashboard — kept separate from AuthController, which
only handles logging in.
"""

import bcrypt
from database.db_connector import DBConnector
from utils.exceptions import RecordNotFoundError, EmptyFieldError


class UserController:

    def get_all_users(self) -> list[dict]:
        with DBConnector() as db:
            db.execute(
                "SELECT id, username, full_name, role, specialization, assigned_doctor_id "
                "FROM users ORDER BY role, full_name"
            )
            return db.fetchall()

    def add_user(self, username: str, password: str, full_name: str, role: str,
                 specialization: str = None, assigned_doctor_id: int = None) -> int:
        if not username or not password or not full_name:
            raise EmptyFieldError("Username, password, and full name are required.")

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        with DBConnector() as db:
            db.execute(
                "INSERT INTO users (username, password_hash, full_name, role, "
                "specialization, assigned_doctor_id) VALUES (%s, %s, %s, %s, %s, %s)",
                (username, password_hash, full_name, role, specialization, assigned_doctor_id),
            )
            return db._cursor.lastrowid

    def delete_user(self, user_id: int):
        with DBConnector() as db:
            db.execute("DELETE FROM users WHERE id=%s", (user_id,))
            if db._cursor.rowcount == 0:
                raise RecordNotFoundError(f"No user with id {user_id}.")
