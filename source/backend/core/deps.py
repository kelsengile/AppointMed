"""FastAPI dependencies: who is logged in, role checks, and booking rate limit."""

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.database import database
from backend.core.exceptions import AuthError, ForbiddenError, TooManyRequestsError
from backend.core.security import decode_token
from backend.repositories.user_repository import UserRepository

_bearer = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    """Load the logged-in staff member from the Authorization header."""
    if credentials is None:
        raise AuthError("Please log in to continue.")
    payload = decode_token(credentials.credentials)
    with database.session() as session:
        user = UserRepository(session).get(int(payload["sub"]))
    if user is None or not user["is_active"]:
        raise AuthError("This account is not active.")
    return user


def require_roles(*roles: str):
    """Build a dependency that only lets the given roles through."""

    def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise ForbiddenError("You do not have access to this action.")
        return user

    return checker


class RateLimiter:
    """Allow at most `max_calls` per `window_seconds` for each key (such as an IP address)."""

    def __init__(self, max_calls: int, window_seconds: int) -> None:
        self._max = max_calls
        self._window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self._window:
                hits.popleft()
            if len(hits) >= self._max:
                raise TooManyRequestsError("Too many booking requests. Please try again in a few minutes.")
            hits.append(now)


_booking_limiter = RateLimiter(max_calls=5, window_seconds=600)


def limit_booking(request: Request) -> None:
    """Protect the public booking endpoint from spam."""
    _booking_limiter.check(request.client.host if request.client else "unknown")