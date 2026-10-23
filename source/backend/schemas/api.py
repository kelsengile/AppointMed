"""Pydantic request bodies. Every input is validated here before it reaches a service."""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Sex = Literal["Male", "Female", "Other"]
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
PHONE_PATTERN = r"^[0-9+()\-\s]{7,20}$"


class Schema(BaseModel):
    """Base model: trims all text and ignores unknown fields."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")


def _check_optional_email(value: str | None) -> str | None:
    """Allow empty, otherwise require something that looks like an email address."""
    import re

    if value and not re.match(EMAIL_PATTERN, value):
        raise ValueError("Enter a valid email address.")
    return value or None


# ---------- auth and profile ----------
class LoginRequest(Schema):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=200)


class ProfileUpdate(Schema):
    full_name: str = Field(min_length=2, max_length=100)
    email: str | None = Field(default=None, max_length=100)

    @field_validator("email")
    @classmethod
    def email_ok(cls, value: str | None) -> str | None:
        return _check_optional_email(value)


class AvatarUpload(Schema):
    image: str = Field(max_length=500_000)


class PasswordChange(Schema):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=72)


# ---------- public booking ----------
class BookingRequest(Schema):
    full_name: str = Field(min_length=2, max_length=100)
    birthdate: date
    sex: Sex
    contact_number: str = Field(pattern=PHONE_PATTERN)
    email: str = Field(max_length=100, pattern=EMAIL_PATTERN)
    address: str = Field(min_length=3, max_length=255)
    doctor_id: int
    preferred_datetime: datetime
    reason: str = Field(min_length=3, max_length=255)

    @field_validator("birthdate")
    @classmethod
    def not_in_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Birthdate cannot be in the future.")
        return value


# ---------- notifications and appointments ----------
class ApproveRequest(Schema):
    room_id: int | None = None
    scheduled_time: datetime | None = None


class DismissRequest(Schema):
    note: str = Field(min_length=3, max_length=255)


class AppointmentCreate(Schema):
    patient_id: int | None = None
    full_name: str | None = Field(default=None, max_length=100)
    birthdate: date | None = None
    sex: Sex | None = None
    contact_number: str | None = Field(default=None, max_length=20)
    scheduled_time: datetime | None = None
    reason: str | None = Field(default=None, max_length=255)
    check_in_now: bool = False


class RescheduleRequest(Schema):
    scheduled_time: datetime


class CancelRequest(Schema):
    reason: str | None = Field(default=None, max_length=200)


class RoomAssign(Schema):
    room_id: int | None = None


class PrescriptionItemIn(Schema):
    medicine_name: str = Field(min_length=1, max_length=150)
    dosage: str | None = Field(default=None, max_length=100)
    quantity: int = Field(ge=1, le=9999)
    unit_price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    instructions: str | None = Field(default=None, max_length=255)


class ExamFinish(Schema):
    diagnosis: str = Field(min_length=2, max_length=2000)
    notes: str | None = Field(default=None, max_length=4000)
    prescription_notes: str | None = Field(default=None, max_length=255)
    consultation_fee: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    items: list[PrescriptionItemIn] = Field(default_factory=list, max_length=30)
    follow_up_time: datetime | None = None


# ---------- patients ----------
class PatientIn(Schema):
    full_name: str = Field(min_length=2, max_length=100)
    birthdate: date | None = None
    sex: Sex | None = None
    contact_number: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=255)
    condition_summary: str | None = Field(default=None, max_length=255)

    @field_validator("email")
    @classmethod
    def email_ok(cls, value: str | None) -> str | None:
        return _check_optional_email(value)

    @field_validator("birthdate")
    @classmethod
    def not_in_future(cls, value: date | None) -> date | None:
        if value and value > date.today():
            raise ValueError("Birthdate cannot be in the future.")
        return value


# ---------- rooms ----------
class RoomStatusUpdate(Schema):
    status: Literal["Available", "Occupied", "Maintenance"]


class RoomIn(Schema):
    room_name: str = Field(min_length=1, max_length=50)
    status: Literal["Available", "Occupied", "Maintenance"] = "Available"


# ---------- admin ----------
class UserCreate(Schema):
    username: str = Field(pattern=r"^[A-Za-z0-9._-]{3,50}$")
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=2, max_length=100)
    role: Literal["doctor", "nurse", "admin"]
    email: str | None = Field(default=None, max_length=100)
    specialization: str | None = Field(default=None, max_length=100)
    assigned_doctor_id: int | None = None

    @field_validator("email")
    @classmethod
    def email_ok(cls, value: str | None) -> str | None:
        return _check_optional_email(value)


class UserUpdate(Schema):
    full_name: str = Field(min_length=2, max_length=100)
    email: str | None = Field(default=None, max_length=100)
    specialization: str | None = Field(default=None, max_length=100)
    assigned_doctor_id: int | None = None

    @field_validator("email")
    @classmethod
    def email_ok(cls, value: str | None) -> str | None:
        return _check_optional_email(value)


class PasswordReset(Schema):
    new_password: str = Field(min_length=8, max_length=72)


class ActiveToggle(Schema):
    is_active: bool


class ScheduleBlock(Schema):
    weekday: int = Field(ge=1, le=7)
    start_time: time
    end_time: time
    slot_minutes: int = Field(ge=5, le=120)


class ScheduleUpdate(Schema):
    blocks: list[ScheduleBlock] = Field(default_factory=list, max_length=70)


class SettingsUpdate(Schema):
    values: dict[str, str]