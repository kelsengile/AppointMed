"""Login."""

from backend.core.database import database
from backend.core.exceptions import AuthError
from backend.core.security import create_token, verify_password
from backend.repositories.user_repository import AuditRepository, UserRepository


class AuthService:
    """Checks credentials and issues tokens."""

    def login(self, username: str, password: str) -> dict:
        failed = False
        result: dict = {}
        with database.session() as session:
            users = UserRepository(session)
            audit = AuditRepository(session)
            user = users.get_by_username(username.strip())
            if user is None or not user["is_active"] or not verify_password(password, user["password_hash"]):
                audit.log(user["id"] if user else None, "LOGIN_FAILED", "users", user["id"] if user else None)
                failed = True
            else:
                users.record_login(user["id"])
                audit.log(user["id"], "LOGIN", "users", user["id"], f"{user['role'].title()} signed in")
                result = {
                    "access_token": create_token(user["id"], user["role"]),
                    "user": {
                        "id": user["id"],
                        "username": user["username"],
                        "full_name": user["full_name"],
                        "role": user["role"],
                    },
                }
        # Raised after the block so the audit row is saved before the error is returned.
        if failed:
            raise AuthError("Incorrect username or password.")
        return result


auth_service = AuthService()