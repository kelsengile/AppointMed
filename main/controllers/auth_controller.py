"""
Handles login/authentication and returns the correct User subclass
so the GUI knows which dashboard to open (polymorphism in action).
"""

import bcrypt
from database.db_connector import DBConnector
from models.user import Doctor, Nurse, Admin
from utils.exceptions import InvalidCredentialsError, EmptyFieldError


class AuthController:

    def login(self, username: str, password: str):
        if not username or not password:
            raise EmptyFieldError("Username and password are required.")

        with DBConnector() as db:
            db.execute("SELECT * FROM users WHERE username=%s", (username,))
            row = db.fetchone()

        if not row or not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
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
