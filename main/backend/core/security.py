"""Password checking and login tokens."""
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from backend.exceptions.app_exceptions import AuthenticationError, ConfigurationError

ALGORITHM = "HS256"


def _secret() -> str:
    secret = os.getenv("SECRET_KEY", "")
    if not secret:
        raise ConfigurationError("The server is not configured. Set SECRET_KEY in main/.env.")
    return secret


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:  # malformed hash or unsupported password length
        return False


def create_access_token(user_id: int, username: str, role: str) -> str:
    minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    expires = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload = {"sub": str(user_id), "username": username, "role": role, "exp": expires}
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, _secret(), algorithms=[ALGORITHM])
    except jwt.PyJWTError as error:
        raise AuthenticationError("Your session has expired. Please sign in again.") from error