"""Passwords, login tokens, rate limiting, and the permission checks used by every protected route."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

import bcrypt
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.models.domain import User
from backend.repositories.user_repository import UserRepository

from .config import settings
from .database import database
from .exceptions import AuthenticationError, PermissionDeniedError

_ALGORITHM = "HS256"
_bearer = HTTPBearer(auto_error=False)


def hash_password(plain: str) -> str:
    """Return a salted bcrypt hash. Plain passwords are never stored."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Check a password against its stored hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_token(user_id: int, role: str) -> str:
    """Create a signed, short-lived login token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Validate a token's signature and expiry."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Your session has expired. Please sign in again.") from exc


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> User:
    """FastAPI dependency: the signed-in, still-active user (loaded fresh from the database)."""
    if credentials is None:
        raise AuthenticationError("Please sign in.")
    payload = decode_token(credentials.credentials)
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise AuthenticationError("Invalid session.") from exc
    row = UserRepository(database).get(user_id)
    if row is None or not row["is_active"]:
        raise AuthenticationError("Your session has ended. Please sign in again.")
    return User.from_row(row)


def require_feature(feature: str) -> Callable[..., User]:
    """Build a dependency that only lets users whose role can access `feature` through."""

    def dependency(user: User = Depends(get_current_user)) -> User:
        if not user.can_access(feature):
            raise PermissionDeniedError()
        return user

    return dependency


class RateLimiter:
    """Sliding-window limiter kept in memory (enough for a single-server coursework app)."""

    def __init__(self, max_events: int, window_seconds: int) -> None:
        self._max = max_events
        self._window = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> deque[float]:
        events = self._events[key]
        while events and now - events[0] > self._window:
            events.popleft()
        return events

    def is_blocked(self, key: str) -> bool:
        """True when `key` already used up its allowance inside the window."""
        with self._lock:
            return len(self._prune(key, time.monotonic())) >= self._max

    def record(self, key: str) -> None:
        """Count one event for `key`."""
        with self._lock:
            now = time.monotonic()
            self._prune(key, now).append(now)

    def reset(self, key: str) -> None:
        """Forget `key` (for example after a successful login)."""
        with self._lock:
            self._events.pop(key, None)


login_limiter = RateLimiter(max_events=5, window_seconds=300)
booking_limiter = RateLimiter(max_events=6, window_seconds=600)