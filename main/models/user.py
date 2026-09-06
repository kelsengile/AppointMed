"""
Base User class + role subclasses.
Demonstrates abstraction, inheritance, encapsulation, and polymorphism
for the rubric's OOP section.
"""

from abc import ABC, abstractmethod


class User(ABC):
    """Abstract base class — every role in the system is a User."""

    def __init__(self, user_id: int, username: str, full_name: str, _password_hash: str):
        self._user_id = user_id
        self._username = username
        self._full_name = full_name
        self.__password_hash = _password_hash  # name-mangled -> encapsulation

    @property
    def user_id(self):
        return self._user_id

    @property
    def username(self):
        return self._username

    @property
    def full_name(self):
        return self._full_name

    def check_password(self, plain_password: str, verify_fn) -> bool:
        return verify_fn(plain_password, self.__password_hash)

    @abstractmethod
    def dashboard_title(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def permissions(self) -> list[str]:
        raise NotImplementedError

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.username}>"


class Doctor(User):
    def __init__(self, user_id, username, full_name, password_hash, specialization: str):
        super().__init__(user_id, username, full_name, password_hash)
        self.specialization = specialization

    def dashboard_title(self) -> str:
        return f"Dr. {self.full_name} — {self.specialization}"

    def permissions(self) -> list[str]:
        return ["view_own_schedule", "view_patient_history", "update_diagnosis"]


class Nurse(User):
    """A Nurse/Secretary is always tied to exactly one Doctor."""

    def __init__(self, user_id, username, full_name, password_hash, assigned_doctor_id: int):
        super().__init__(user_id, username, full_name, password_hash)
        self.assigned_doctor_id = assigned_doctor_id

    def dashboard_title(self) -> str:
        return f"{self.full_name} — Secretary/Nurse"

    def permissions(self) -> list[str]:
        return ["manage_assigned_doctor_schedule", "add_appointment", "edit_appointment"]


class Admin(User):
    def dashboard_title(self) -> str:
        return f"{self.full_name} — Administrator"

    def permissions(self) -> list[str]:
        return ["manage_users", "view_all_records", "system_settings"]
