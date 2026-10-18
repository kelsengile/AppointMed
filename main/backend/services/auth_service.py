"""Business logic for staff login."""
from backend.core.security import create_access_token, decode_access_token, verify_password
from backend.exceptions.app_exceptions import AuthenticationError, InactiveAccountError
from backend.models.user import User
from backend.repositories.audit_repository import AuditRepository
from backend.repositories.user_repository import UserRepository
from backend.schemas.auth import LoginResponse, UserOut


class AuthService:
    def __init__(self) -> None:
        self._users = UserRepository()
        self._audit = AuditRepository()

    def login(self, username: str, password: str) -> LoginResponse:
        user = self._users.get_by_username(username.strip())
        # Same message for "no such user" and "wrong password" on purpose.
        if user is None or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid username or password.")
        if not user.is_active:
            raise InactiveAccountError("This account has been deactivated.")

        self._users.record_login(user.id)
        self._audit.add(user.id, "LOGIN", "users", user.id, f"{user.role.value.capitalize()} signed in")

        token = create_access_token(user.id, user.username, user.role.value)
        return LoginResponse(access_token=token, user=UserOut.from_model(user))

    def get_user_from_token(self, token: str) -> User:
        payload = decode_access_token(token)
        try:
            user_id = int(payload["sub"])
        except (KeyError, ValueError) as error:
            raise AuthenticationError("Invalid session. Please sign in again.") from error
        user = self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("Invalid session. Please sign in again.")
        return user