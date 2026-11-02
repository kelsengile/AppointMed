"""Small helpers shared by the services."""

from __future__ import annotations

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any


def to_money(value: Any) -> Decimal:
    """Convert a number to a Decimal with two places (money is never handled as float)."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def blank_to_none(value: str | None) -> str | None:
    """Trim text and turn an empty result into None so it is stored as NULL."""
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def floor_minute(value: datetime) -> datetime:
    """Drop seconds so appointment times line up with the doctor's slots."""
    return value.replace(second=0, microsecond=0)


def trim(text: str, limit: int) -> str:
    """Shorten text so it fits a VARCHAR column."""
    return text if len(text) <= limit else text[: limit - 1] + "…"