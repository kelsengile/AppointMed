"""Request bodies for the admin Database page."""

import re

from pydantic import Field, field_validator

from backend.schemas.api import Schema

_COLUMN_NAME = re.compile(r"[A-Za-z0-9_]{1,64}")


class RowValues(Schema):
    """Column name -> new value. Blank text means 'use the default' on insert and NULL on edit."""

    values: dict[str, str | int | float | bool | None]

    @field_validator("values")
    @classmethod
    def values_ok(cls, value: dict) -> dict:
        if len(value) > 60:
            raise ValueError("Too many columns in one request.")
        for key, item in value.items():
            if not _COLUMN_NAME.fullmatch(key):
                raise ValueError("A column name is not valid.")
            if isinstance(item, str) and len(item) > 70_000:
                raise ValueError("A value is too long.")
        return value


class SqlRequest(Schema):
    """One SQL statement typed in the console."""

    sql: str = Field(min_length=1, max_length=5000)