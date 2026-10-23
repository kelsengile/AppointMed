"""Domain objects: users by role (inheritance + polymorphism) and the appointment status workflow."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Mapping

from backend.core.exceptions import InvalidStatusError, PermissionDeniedError, ValidationFailedError


class User(ABC):
    """A staff member. Subclasses decide which features their role may open."""

    role: ClassVar[str] = ""
    features: ClassVar[frozenset[str]] = frozenset()

    def __init__(
        self,
        user_id: int,
        username: str,
        full_name: str,
        email: str | None = None,
        specialization: str | None = None,
        assigned_doctor_id: int | None = None,
    ) -> None:
        if not username or not full_name:
            raise ValidationFailedError("A user needs a username and a full name.")
        self._id = user_id
        self._username = username
        self._full_name = full_name
        self._email = email
        self._specialization = specialization
        self._assigned_doctor_id = assigned_doctor_id

    @property
    def id(self) -> int:
        return self._id

    @property
    def username(self) -> str:
        return self._username

    @property
    def full_name(self) -> str:
        return self._full_name

    @property
    def assigned_doctor_id(self) -> int | None:
        return self._assigned_doctor_id

    def can_access(self, feature: str) -> bool:
        """Polymorphic permission check: each role has its own feature set."""
        return feature in self.features

    @property
    @abstractmethod
    def scope_doctor_id(self) -> int:
        """The doctor whose clinical data this user works with."""

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "User":
        """Factory: build the right subclass from a database row."""
        role_class = _ROLE_CLASSES.get(row["role"])
        if role_class is None:
            raise ValidationFailedError("Unknown user role.")
        return role_class(
            row["id"], row["username"], row["full_name"], row.get("email"), row.get("specialization"), row.get("assigned_doctor_id")
        )


_CLINICAL = {"dashboard", "appointments", "notifications", "patients", "history", "invoice"}


class Doctor(User):
    """Sees their own patients, runs examinations, and writes prescriptions."""

    role = "doctor"
    features = frozenset(_CLINICAL | {"prescriptions", "exam"})

    @property
    def scope_doctor_id(self) -> int:
        return self.id


class Nurse(User):
    """Supports one doctor: approves requests, checks patients in, and takes payment."""

    role = "nurse"
    features = frozenset(_CLINICAL)

    @property
    def scope_doctor_id(self) -> int:
        if self.assigned_doctor_id is None:
            raise PermissionDeniedError("No doctor is assigned to your account. Ask an administrator.")
        return self.assigned_doctor_id


class Admin(User):
    """Manages users, rooms, settings, reports, and audit logs. Does not take part in appointments."""

    role = "admin"
    features = frozenset({"admin_dashboard", "users", "rooms", "settings", "reports", "audit"})

    @property
    def scope_doctor_id(self) -> int:
        raise PermissionDeniedError("Administrators do not work with clinical records.")


_ROLE_CLASSES: dict[str, type[User]] = {"doctor": Doctor, "nurse": Nurse, "admin": Admin}


class AppointmentWorkflow:
    """The allowed appointment status changes (a small state machine)."""

    STATUSES = ("Scheduled", "Checked-in", "Consulting", "Examined", "Completed", "Cancelled")
    TRANSITIONS: ClassVar[dict[str, frozenset[str]]] = {
        "Scheduled": frozenset({"Checked-in", "Cancelled"}),
        "Checked-in": frozenset({"Consulting", "Cancelled"}),
        "Consulting": frozenset({"Examined", "Checked-in"}),  # back to the queue if started by mistake
        "Examined": frozenset({"Completed"}),
        "Completed": frozenset(),
        "Cancelled": frozenset(),
    }

    @classmethod
    def can_move(cls, current: str, target: str) -> bool:
        """True when `current` may change to `target`."""
        return target in cls.TRANSITIONS.get(current, frozenset())

    @classmethod
    def ensure(cls, current: str, target: str) -> None:
        """Raise InvalidStatusError when the change is not allowed."""
        if not cls.can_move(current, target):
            raise InvalidStatusError(f"This appointment is {current}, so it cannot become {target}.")