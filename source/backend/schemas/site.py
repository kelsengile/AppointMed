"""Request bodies for the website branding settings."""

import re

from pydantic import Field, field_validator

from backend.schemas.api import Schema


class SiteContentUpdate(Schema):
    """Field name -> new text. An empty text restores the default."""

    values: dict[str, str]

    @field_validator("values")
    @classmethod
    def values_ok(cls, value: dict[str, str]) -> dict[str, str]:
        if len(value) > 20:
            raise ValueError("Too many fields in one request.")
        for key, text in value.items():
            if not re.fullmatch(r"[a-z_]{1,50}", key) or len(text) > 1100:
                raise ValueError("A field name or value is not valid.")
        return value


class SiteImageUpload(Schema):
    image: str = Field(max_length=2_500_000)