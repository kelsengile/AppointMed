"""Website branding: front-page texts, links, logo, and hero picture."""

from __future__ import annotations

import base64
import binascii
import re
import unicodedata
from typing import Any

from backend.core.database import Database, database
from backend.core.exceptions import NotFoundError, ValidationFailedError
from backend.models.domain import User
from backend.repositories.site_repository import SiteContentRepository
from backend.repositories.system_repository import AuditRepository
from backend.services.auth_service import _detect_mime
from backend.services.notifier import Notifier, notifier

# key -> (max length, kind)
TEXT_FIELDS: dict[str, tuple[int, str]] = {
    "hero_title": (120, "line"),
    "hero_text": (500, "multi"),
    "about_title": (60, "line"),
    "about_subtitle": (120, "line"),
    "about_lead": (1000, "multi"),
    "about_second": (1000, "multi"),
    "footer_text": (400, "multi"),
    "contact_phone": (30, "phone"),
    "contact_email": (100, "email"),
    "contact_hours": (100, "line"),
    "social_facebook": (255, "url"),
    "social_x": (255, "url"),
    "social_linkedin": (255, "url"),
    "social_youtube": (255, "url"),
}
# kind -> (database key, maximum size in bytes)
IMAGES = {"logo": ("logo_image", 300_000), "hero": ("hero_image", 1_500_000)}


class SiteService:
    """Public reads and admin-only changes to the website's look and text."""

    def __init__(self, db: Database = database, notify: Notifier = notifier) -> None:
        self._db = db
        self._notifier = notify

    @staticmethod
    def _clean(key: str, value: str) -> str:
        limit, kind = TEXT_FIELDS[key]
        text = value.strip()
        if len(text) > limit:
            raise ValidationFailedError(f"That text is too long (at most {limit} characters).")
        for ch in text:
            if unicodedata.category(ch) == "Cc" and not (kind == "multi" and ch in "\n\r\t"):
                raise ValidationFailedError("Control characters are not allowed here.")
        if text and kind == "url" and not re.fullmatch(r"https?://\S+", text):
            raise ValidationFailedError("Links must start with http:// or https://.")
        if text and kind == "email" and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", text):
            raise ValidationFailedError("Enter a valid email address.")
        if text and kind == "phone" and not re.fullmatch(r"[0-9+()\-\s]{5,30}", text):
            raise ValidationFailedError("Enter a valid phone number.")
        return text

    def public(self) -> dict[str, Any]:
        repo = SiteContentRepository(self._db)
        images = repo.image_keys()
        return {
            "version": repo.version(),
            "has_logo": "logo_image" in images,
            "has_hero": "hero_image" in images,
            "values": {k: v for k, v in repo.texts().items() if k in TEXT_FIELDS},
        }

    def image(self, kind: str) -> tuple[bytes, str]:
        spec = IMAGES.get(kind)
        value = SiteContentRepository(self._db).get_value(spec[0]) if spec else None
        match = re.match(r"^data:(image/[a-z]+);base64,(.+)$", value or "", re.DOTALL)
        if not match:
            raise NotFoundError("No picture has been set.")
        return base64.b64decode(match.group(2)), match.group(1)

    def update(self, admin: User, values: dict[str, str]) -> dict[str, Any]:
        cleaned: dict[str, str] = {}
        for key, value in values.items():
            if key not in TEXT_FIELDS:
                raise ValidationFailedError(f"Unknown field: {key}")
            cleaned[key] = self._clean(key, value)
        with self._db.transaction() as tx:
            repo = SiteContentRepository(tx)
            for key, value in cleaned.items():
                if value:
                    repo.upsert(key, value, admin.id)
                else:
                    repo.remove(key)  # back to the built-in default
            AuditRepository(tx).record(admin.id, "UPDATE_SITE_CONTENT", "site_content", None, f"Changed {len(cleaned)} website field(s)")
        self._notifier.clinic_changed(
            actor_id=admin.id,
            actor_name=admin.full_name,
            title="The website was updated",
            lines=[("Website text", f"{len(cleaned)} field(s) changed")],
        )
        return self.public()

    def set_image(self, admin: User, kind: str, image: str) -> dict[str, Any]:
        spec = IMAGES.get(kind)
        if spec is None:
            raise NotFoundError("Unknown picture.")
        match = re.match(r"^data:image/(?:png|jpeg|jpg|webp);base64,(.+)$", image, re.DOTALL)
        if not match:
            raise ValidationFailedError("Upload a PNG, JPEG or WebP image.")
        try:
            raw = base64.b64decode(match.group(1), validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValidationFailedError("The image could not be read.") from exc
        if len(raw) > spec[1]:
            raise ValidationFailedError("The image is too large. Choose a smaller one.")
        mime = _detect_mime(raw)
        if mime is None:
            raise ValidationFailedError("Upload a PNG, JPEG or WebP image.")
        with self._db.transaction() as tx:
            SiteContentRepository(tx).upsert(spec[0], f"data:{mime};base64,{base64.b64encode(raw).decode()}", admin.id)
            AuditRepository(tx).record(admin.id, "UPDATE_SITE_IMAGE", "site_content", None, f"Changed the {kind} picture")
        self._notifier.clinic_changed(
            actor_id=admin.id,
            actor_name=admin.full_name,
            title="The website was updated",
            lines=[("Picture", f"The {kind} picture was changed")],
        )
        return self.public()

    def remove_image(self, admin: User, kind: str) -> dict[str, Any]:
        spec = IMAGES.get(kind)
        if spec is None:
            raise NotFoundError("Unknown picture.")
        with self._db.transaction() as tx:
            SiteContentRepository(tx).remove(spec[0])
            AuditRepository(tx).record(admin.id, "REMOVE_SITE_IMAGE", "site_content", None, f"Removed the {kind} picture")
        self._notifier.clinic_changed(
            actor_id=admin.id,
            actor_name=admin.full_name,
            title="The website was updated",
            lines=[("Picture", f"The {kind} picture was changed")],
        )
        return self.public()