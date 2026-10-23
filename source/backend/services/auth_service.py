"""Login, profile, avatar, and password changes."""

from __future__ import annotations

import base64
import binascii
import re
from typing import Any

from backend.core.database import Database, database
from backend.core.exceptions import AuthenticationError, NotFoundError, RateLimitError, ValidationFailedError
from backend.core.security import create_token, hash_password, login_limiter, verify_password
from backend.core.utils import blank_to_none, trim
from backend.repositories.system_repository import AuditRepository
from backend.repositories.user_repository import UserRepository

_MAX_AVATAR_BYTES = 300_000


def _detect_mime(raw: bytes) -> str | None:
    """Identify the image type from its first bytes (never trust the declared type)."""
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return None


class AuthService:
    """Authentication and self-service account operations."""

    def __init__(self, db: Database = database) -> None:
        self._db = db
        self._users = UserRepository(db)
        self._audit = AuditRepository(db)

    def login(self, username: str, password: str) -> dict[str, Any]:
        """Check credentials and return a token. Repeated failures are rate-limited."""
        name = username.strip()
        key = name.lower()
        if login_limiter.is_blocked(key):
            raise RateLimitError("Too many failed attempts. Try again in a few minutes.")
        row = self._users.get_by_username(name)
        if row is None or not verify_password(password, row["password_hash"]):
            login_limiter.record(key)
            self._audit.record(None, "LOGIN_FAILED", "users", row["id"] if row else None, f"Failed login for '{trim(name, 40)}'")
            raise AuthenticationError("Incorrect username or password.")
        if not row["is_active"]:
            raise AuthenticationError("This account is deactivated. Contact an administrator.")
        login_limiter.reset(key)
        self._users.touch_login(row["id"])
        self._audit.record(row["id"], "LOGIN", "users", row["id"], f"{row['role'].title()} signed in")
        return {
            "access_token": create_token(row["id"], row["role"]),
            "user": {"id": row["id"], "username": row["username"], "full_name": row["full_name"], "role": row["role"]},
        }

    def profile(self, user_id: int) -> dict[str, Any]:
        """The signed-in user's profile, with the avatar as a data URL."""
        row = self._users.get_detail(user_id)
        if row is None:
            raise NotFoundError("Account not found.")
        raw = self._users.get_avatar(user_id)
        mime = _detect_mime(raw) if raw else None
        row["avatar"] = f"data:{mime};base64,{base64.b64encode(raw).decode()}" if raw and mime else None
        return row

    def update_profile(self, user_id: int, full_name: str, email: str | None) -> dict[str, Any]:
        """Change the user's own name and email."""
        self._users.update(user_id, {"full_name": full_name, "email": blank_to_none(email)})
        self._audit.record(user_id, "UPDATE_PROFILE", "users", user_id, "Updated own profile")
        return self.profile(user_id)

    def set_avatar(self, user_id: int, image: str) -> dict[str, Any]:
        """Store a small profile picture sent as a base64 data URL."""
        match = re.match(r"^data:image/(?:png|jpeg|jpg|webp);base64,(.+)$", image, re.DOTALL)
        if not match:
            raise ValidationFailedError("Upload a PNG, JPEG or WebP image.")
        try:
            raw = base64.b64decode(match.group(1), validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValidationFailedError("The image could not be read.") from exc
        if len(raw) > _MAX_AVATAR_BYTES:
            raise ValidationFailedError("The image is too large. Choose a smaller one.")
        if _detect_mime(raw) is None:
            raise ValidationFailedError("Upload a PNG, JPEG or WebP image.")
        self._users.set_avatar(user_id, raw)
        return self.profile(user_id)

    def remove_avatar(self, user_id: int) -> dict[str, Any]:
        self._users.set_avatar(user_id, None)
        return self.profile(user_id)

    def change_password(self, user_id: int, current: str, new: str) -> None:
        """Change the user's own password after checking the current one."""
        stored = self._users.get_password_hash(user_id)
        if stored is None or not verify_password(current, stored):
            raise ValidationFailedError("Your current password is not correct.")
        if current == new:
            raise ValidationFailedError("Choose a password that is different from the current one.")
        self._users.set_password(user_id, hash_password(new))
        self._audit.record(user_id, "CHANGE_PASSWORD", "users", user_id, "Changed own password")