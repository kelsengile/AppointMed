"""Pydantic request bodies. Every input is validated here before it reaches a service."""

import re
import unicodedata
from datetime import date, datetime, time
from decimal import Decimal
from typing import Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Sex = Literal["Male", "Female", "Other"]
RoomState = Literal["Available", "Occupied", "Maintenance"]
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
MAX_MONEY = Decimal("1000000")
MIN_BIRTH_YEAR = 1900


class Schema(BaseModel):
    """Base model: trims all text and ignores unknown fields."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")


# ---------- reusable checks ----------
def _restrict(value: str, extra: str, what: str, digits: bool = True) -> str:
    """Allow letters, optional digits, combining marks and the characters in `extra` only."""
    for ch in value:
        if ch.isalpha() or (digits and ch.isdecimal()) or ch in extra or unicodedata.category(ch).startswith("M"):
            continue
        raise ValueError(f"{what} cannot contain the character {ch!r}.")
    return value


def _person_name(value: str) -> str:
    _restrict(value, " '’.,()-", "A name", digits=False)
    if sum(ch.isalpha() for ch in value) < 2:
        raise ValueError("Enter a valid name.")
    return value


def _specialization(value: str) -> str:
    return _restrict(value, " &,.-/", "The specialization", digits=False)


def _room_name(value: str) -> str:
    return _restrict(value, " #.()-", "The room name")


def _medicine_text(value: str) -> str:
    return _restrict(value, " .,()/%+'’-", "This field")


def _address(value: str) -> str:
    return _restrict(value, " #.,'’()/-", "The address")


def _opt(value: str | None, check: Callable[[str], str]) -> str | None:
    """Run `check` on a value that may be empty (empty becomes None)."""
    return check(value) if value else None


def _no_control(value: str, multiline: bool = False) -> str:
    allowed = "\n\r\t" if multiline else ""
    for ch in value:
        if unicodedata.category(ch) == "Cc" and ch not in allowed:
            raise ValueError("Control characters are not allowed here.")
    return value


def _phone(value: str) -> str:
    digits = sum(ch.isdigit() for ch in value)
    if not re.fullmatch(r"\+?[0-9()\-\s]{6,19}", value) or not 7 <= digits <= 15:
        raise ValueError("Enter a valid contact number (7 to 15 digits; spaces, + - ( ) allowed).")
    return value


def _naive(value: datetime) -> datetime:
    """Times are clinic-local. A time zone would break comparisons with the database clock."""
    if value.tzinfo is not None:
        raise ValueError("Send the date and time without a time zone.")
    if not 2000 <= value.year <= 2100:
        raise ValueError("Enter a valid date and time.")
    return value


def _birthdate(value: date) -> date:
    if value > date.today() or value.year < MIN_BIRTH_YEAR:
        raise ValueError("Enter a valid birthdate.")
    return value


def _check_optional_email(value: str | None) -> str | None:
    """Allow empty, otherwise require something that looks like an email address."""
    if value and not re.match(EMAIL_PATTERN, value):
        raise ValueError("Enter a valid email address.")
    return value or None


def _check_password_strength(value: str) -> str:
    """A new password needs 8+ characters, upper and lower case letters, a number, and a special character."""
    if len(value.encode("utf-8")) > 72:
        raise ValueError("The password is too long (72 bytes at most; accented or non-Latin characters count as more than one).")
    missing: list[str] = []
    if len(value) < 8:
        missing.append("at least 8 characters")
    if not re.search(r"[A-Z]", value):
        missing.append("an uppercase letter")
    if not re.search(r"[a-z]", value):
        missing.append("a lowercase letter")
    if not re.search(r"[0-9]", value):
        missing.append("a number")
    if not re.search(r"[^A-Za-z0-9\s]", value):
        missing.append("a special character such as ! ? @ *")
    if missing:
        raise ValueError("The password needs " + ", ".join(missing) + ".")
    return value


# ---------- auth and profile ----------
class LoginRequest(Schema):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=200)


class ProfileUpdate(Schema):
    full_name: str = Field(min_length=2, max_length=100)
    email: str | None = Field(default=None, max_length=100)

    @field_validator("full_name")
    @classmethod
    def name_ok(cls, value: str) -> str:
        return _person_name(value)

    @field_validator("email")
    @classmethod
    def email_ok(cls, value: str | None) -> str | None:
        return _check_optional_email(value)


class AvatarUpload(Schema):
    image: str = Field(max_length=500_000)


class PasswordChange(Schema):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=72)

    @field_validator("new_password")
    @classmethod
    def password_strong(cls, value: str) -> str:
        return _check_password_strength(value)


# ---------- public booking ----------
class BookingRequest(Schema):
    full_name: str = Field(min_length=2, max_length=100)
    birthdate: date
    sex: Sex
    contact_number: str = Field(max_length=20)
    email: str = Field(max_length=100, pattern=EMAIL_PATTERN)
    address: str = Field(min_length=3, max_length=255)
    doctor_id: int = Field(ge=1)
    preferred_datetime: datetime
    reason: str = Field(min_length=3, max_length=255)

    @field_validator("full_name")
    @classmethod
    def name_ok(cls, value: str) -> str:
        return _person_name(value)

    @field_validator("birthdate")
    @classmethod
    def birthdate_ok(cls, value: date) -> date:
        return _birthdate(value)

    @field_validator("contact_number")
    @classmethod
    def phone_ok(cls, value: str) -> str:
        return _phone(value)

    @field_validator("email")
    @classmethod
    def email_lower(cls, value: str) -> str:
        return value.lower()

    @field_validator("address")
    @classmethod
    def address_ok(cls, value: str) -> str:
        return _address(value)

    @field_validator("preferred_datetime")
    @classmethod
    def when_ok(cls, value: datetime) -> datetime:
        return _naive(value)

    @field_validator("reason")
    @classmethod
    def reason_ok(cls, value: str) -> str:
        return _no_control(value)


# ---------- notifications and appointments ----------
class ApproveRequest(Schema):
    room_id: int | None = Field(default=None, ge=1)
    scheduled_time: datetime | None = None

    @field_validator("scheduled_time")
    @classmethod
    def when_ok(cls, value: datetime | None) -> datetime | None:
        return _naive(value) if value else None


class DismissRequest(Schema):
    note: str = Field(min_length=3, max_length=255)

    @field_validator("note")
    @classmethod
    def note_ok(cls, value: str) -> str:
        return _no_control(value)


class AppointmentCreate(Schema):
    patient_id: int | None = Field(default=None, ge=1)
    full_name: str | None = Field(default=None, max_length=100)
    birthdate: date | None = None
    sex: Sex | None = None
    contact_number: str | None = Field(default=None, max_length=20)
    scheduled_time: datetime | None = None
    reason: str | None = Field(default=None, max_length=255)
    check_in_now: bool = False

    @field_validator("full_name")
    @classmethod
    def name_ok(cls, value: str | None) -> str | None:
        return _opt(value, _person_name)

    @field_validator("birthdate")
    @classmethod
    def birthdate_ok(cls, value: date | None) -> date | None:
        return _birthdate(value) if value else None

    @field_validator("contact_number")
    @classmethod
    def phone_ok(cls, value: str | None) -> str | None:
        return _opt(value, _phone)

    @field_validator("scheduled_time")
    @classmethod
    def when_ok(cls, value: datetime | None) -> datetime | None:
        return _naive(value) if value else None

    @field_validator("reason")
    @classmethod
    def reason_ok(cls, value: str | None) -> str | None:
        return _opt(value, _no_control)


class RescheduleRequest(Schema):
    scheduled_time: datetime

    @field_validator("scheduled_time")
    @classmethod
    def when_ok(cls, value: datetime) -> datetime:
        return _naive(value)


class CancelRequest(Schema):
    reason: str | None = Field(default=None, max_length=200)

    @field_validator("reason")
    @classmethod
    def reason_ok(cls, value: str | None) -> str | None:
        return _opt(value, _no_control)


class RoomAssign(Schema):
    room_id: int | None = Field(default=None, ge=1)


class PrescriptionItemIn(Schema):
    medicine_name: str = Field(min_length=1, max_length=150)
    dosage: str | None = Field(default=None, max_length=100)
    quantity: int = Field(ge=1, le=9999)
    unit_price: Decimal = Field(ge=0, le=MAX_MONEY, max_digits=10, decimal_places=2)
    instructions: str | None = Field(default=None, max_length=255)

    @field_validator("medicine_name")
    @classmethod
    def medicine_ok(cls, value: str) -> str:
        return _medicine_text(value)

    @field_validator("dosage")
    @classmethod
    def dosage_ok(cls, value: str | None) -> str | None:
        return _opt(value, _medicine_text)

    @field_validator("instructions")
    @classmethod
    def instructions_ok(cls, value: str | None) -> str | None:
        return _opt(value, _no_control)


class ExamFinish(Schema):
    diagnosis: str = Field(min_length=2, max_length=2000)
    notes: str | None = Field(default=None, max_length=4000)
    prescription_notes: str | None = Field(default=None, max_length=255)
    consultation_fee: Decimal = Field(ge=0, le=MAX_MONEY, max_digits=10, decimal_places=2)
    items: list[PrescriptionItemIn] = Field(default_factory=list, max_length=30)
    follow_up_time: datetime | None = None

    @field_validator("diagnosis", "notes")
    @classmethod
    def long_text_ok(cls, value: str | None) -> str | None:
        return _no_control(value, multiline=True) if value else value

    @field_validator("prescription_notes")
    @classmethod
    def rx_note_ok(cls, value: str | None) -> str | None:
        return _opt(value, _no_control)

    @field_validator("follow_up_time")
    @classmethod
    def when_ok(cls, value: datetime | None) -> datetime | None:
        return _naive(value) if value else None


# ---------- patients ----------
class PatientIn(Schema):
    full_name: str = Field(min_length=2, max_length=100)
    birthdate: date | None = None
    sex: Sex | None = None
    contact_number: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=255)
    condition_summary: str | None = Field(default=None, max_length=255)

    @field_validator("full_name")
    @classmethod
    def name_ok(cls, value: str) -> str:
        return _person_name(value)

    @field_validator("birthdate")
    @classmethod
    def birthdate_ok(cls, value: date | None) -> date | None:
        return _birthdate(value) if value else None

    @field_validator("contact_number")
    @classmethod
    def phone_ok(cls, value: str | None) -> str | None:
        return _opt(value, _phone)

    @field_validator("email")
    @classmethod
    def email_ok(cls, value: str | None) -> str | None:
        return _check_optional_email(value)

    @field_validator("address")
    @classmethod
    def address_ok(cls, value: str | None) -> str | None:
        return _opt(value, _address)

    @field_validator("condition_summary")
    @classmethod
    def condition_ok(cls, value: str | None) -> str | None:
        return _opt(value, _no_control)


# ---------- rooms ----------
class RoomStatusUpdate(Schema):
    status: RoomState


class RoomIn(Schema):
    room_name: str = Field(min_length=1, max_length=50)
    status: RoomState = "Available"

    @field_validator("room_name")
    @classmethod
    def room_ok(cls, value: str) -> str:
        return _room_name(value)


# ---------- admin ----------
class UserCreate(Schema):
    username: str = Field(pattern=r"^[A-Za-z0-9._-]{3,50}$")
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=2, max_length=100)
    role: Literal["doctor", "nurse", "admin"]
    email: str | None = Field(default=None, max_length=100)
    specialization: str | None = Field(default=None, max_length=100)
    assigned_doctor_id: int | None = Field(default=None, ge=1)

    @field_validator("full_name")
    @classmethod
    def name_ok(cls, value: str) -> str:
        return _person_name(value)

    @field_validator("specialization")
    @classmethod
    def specialization_ok(cls, value: str | None) -> str | None:
        return _opt(value, _specialization)

    @field_validator("email")
    @classmethod
    def email_ok(cls, value: str | None) -> str | None:
        return _check_optional_email(value)

    @field_validator("password")
    @classmethod
    def password_strong(cls, value: str) -> str:
        return _check_password_strength(value)


class UserUpdate(Schema):
    full_name: str = Field(min_length=2, max_length=100)
    email: str | None = Field(default=None, max_length=100)
    specialization: str | None = Field(default=None, max_length=100)
    assigned_doctor_id: int | None = Field(default=None, ge=1)

    @field_validator("full_name")
    @classmethod
    def name_ok(cls, value: str) -> str:
        return _person_name(value)

    @field_validator("specialization")
    @classmethod
    def specialization_ok(cls, value: str | None) -> str | None:
        return _opt(value, _specialization)

    @field_validator("email")
    @classmethod
    def email_ok(cls, value: str | None) -> str | None:
        return _check_optional_email(value)


class PasswordReset(Schema):
    new_password: str = Field(min_length=8, max_length=72)

    @field_validator("new_password")
    @classmethod
    def password_strong(cls, value: str) -> str:
        return _check_password_strength(value)


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

    @field_validator("values")
    @classmethod
    def values_ok(cls, value: dict[str, str]) -> dict[str, str]:
        if len(value) > 10:
            raise ValueError("Too many settings in one request.")
        for key, text in value.items():
            if not re.fullmatch(r"[a-z_]{1,50}", key) or len(text) > 255:
                raise ValueError("A setting name or value is not valid.")
            _no_control(text)
        return value