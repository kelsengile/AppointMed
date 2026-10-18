"""All SQL for the users table."""
from backend.core.connection import database
from backend.models.user import Role, User
from typing import Any, cast

_COLUMNS = "id, username, password_hash, full_name, role, specialization, is_active"


class UserRepository:
    def get_by_username(self, username: str) -> User | None:
        return self._fetch_one(f"SELECT {_COLUMNS} FROM users WHERE username = %s", (username,))

    def get_by_id(self, user_id: int) -> User | None:
        return self._fetch_one(f"SELECT {_COLUMNS} FROM users WHERE id = %s", (user_id,))

    def record_login(self, user_id: int) -> None:
        connection = database.get_connection()
        try:
            cursor = connection.cursor()
            try:
                cursor.execute("UPDATE users SET last_login_at = NOW() WHERE id = %s", (user_id,))
                connection.commit()
            finally:
                cursor.close()
        finally:
            connection.close()

    def _fetch_one(self, query: str, params: tuple) -> User | None:
        connection = database.get_connection()
        try:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(query, params)
                row = cursor.fetchone()
            finally:
                cursor.close()
        finally:
            connection.close()
        row = cast("dict[str, Any] | None", row)  # place right after the try/finally block
        return self._to_user(row) if row else None

    @staticmethod
    def _to_user(row: dict) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            full_name=row["full_name"],
            role=Role(row["role"]),
            specialization=row["specialization"],
            is_active=bool(row["is_active"]),
        )