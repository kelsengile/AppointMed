"""Password checking and login tokens."""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from backend.core.config import settings
from backend.core.exceptions import AuthError


def verify_password(plain: str, hashed: str) -> bool:
    """Compare a typed password with its bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_token(user_id: int, role: str) -> str:
    """Sign a short-lived login token."""
    if not settings.jwt_secret:
        raise RuntimeError("JWT_SECRET is not set in source/.env")
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": str(user_id), "role": role, "exp": expires}, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    """Return the token payload, or raise AuthError if it is invalid or expired."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise AuthError("Your session has expired. Please log in again.") from exc