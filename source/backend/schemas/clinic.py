"""Request bodies, validated by Pydantic before they reach a service."""

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE = re.compile(r"^[0-9+()\-\s]{7,20}$")


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class BookingRequest(BaseModel):
    """What a patient fills in on the public booking page."""

    full_name: str = Field(min_length=2, max_length=100)
    birthdate: date
    sex: Literal["Male", "Female", "Other"]
    contact_number: str
    email: str = Field(max_length=100)
    address: str = Field(min_length=3, max_length=255)
    doctor_id: int
    preferred_datetime: datetime
    reason: str = Field(min_length=3, max_length=255)

    @field_validator("full_name", "address", "reason", "contact_number", "email")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("contact_number")
    @classmethod
    def check_phone(cls, value: str) -> str:
        if not _PHONE.match(value):
            raise ValueError("Enter a valid contact number (digits, spaces, + - ( ) only).")
        return value

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str) -> str:
        if not _EMAIL.match(value):
            raise ValueError("Enter a valid email address.")
        return value.lower()

    @field_validator("birthdate")
    @classmethod
    def check_birthdate(cls, value: date) -> date:
        if value > date.today() or value.year < 1900:
            raise ValueError("Enter a valid birthdate.")
        return value


class DismissRequest(BaseModel):
    note: str | None = Field(default=None, max_length=255)


class PrescriptionItemIn(BaseModel):
    medicine_name: str = Field(min_length=1, max_length=150)
    dosage: str | None = Field(default=None, max_length=100)
    quantity: int = Field(ge=1, le=1000)
    unit_price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    instructions: str | None = Field(default=None, max_length=255)


class ExaminationFinish(BaseModel):
    """What the doctor submits when the examination is done."""

    diagnosis: str = Field(min_length=1, max_length=5000)
    notes: str | None = Field(default=None, max_length=5000)
    prescription_notes: str | None = Field(default=None, max_length=255)
    consultation_fee: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    items: list[PrescriptionItemIn] = Field(default_factory=list, max_length=30)