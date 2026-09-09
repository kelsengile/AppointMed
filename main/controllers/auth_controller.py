"""
Handles logging in. If the username and password are correct, it builds
and returns the right kind of User object (Doctor, Nurse, or Admin) so
the GUI knows which dashboard window to open.
"""

import bcrypt
from database.db_connector import DBConnector
from models.user import Doctor, Nurse, Admin
from utils.exceptions import InvalidCredentialsError, EmptyFieldError


class AuthController:

    def login(self, username, password):
        if not username or not password:
            raise EmptyFieldError("Username and password are required.")

        with DBConnector() as db:
            db.execute("SELECT * FROM users WHERE username=%s", (username,))
            row = db.fetchone()

        if not row:
            raise InvalidCredentialsError("Incorrect username or password.")

        password_matches = bcrypt.checkpw(password.encode(), row["password_hash"].encode())
        if not password_matches:
            raise InvalidCredentialsError("Incorrect username or password.")

        role = row["role"]
        if role == "doctor":
            return Doctor(row["id"], row["username"], row["full_name"],
                          row["password_hash"], row["specialization"])
        elif role == "nurse":
            return Nurse(row["id"], row["username"], row["full_name"],
                        row["password_hash"], row["assigned_doctor_id"])
        elif role == "admin":
            return Admin(row["id"], row["username"], row["full_name"], row["password_hash"])
        else:
            raise InvalidCredentialsError("Unknown user role.")
