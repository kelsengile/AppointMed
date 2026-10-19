"""Authentication and role checks for protected routes."""
from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.exceptions.app_exceptions import AuthenticationError, PermissionDeniedError
from backend.models.user import Role, User
from backend.services.auth_service import AuthService

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> User:
    if credentials is None:
        raise AuthenticationError("Not authenticated.")
    return AuthService().get_user_from_token(credentials.credentials)


def require_roles(*roles: Role) -> Callable[[User], User]:
    """Use as a route dependency: Depends(require_roles(Role.ADMIN))."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise PermissionDeniedError("You do not have permission to do this.")
        return user

    return checker