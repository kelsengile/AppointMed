"""Domain model for clinic staff."""
from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    DOCTOR = "doctor"
    NURSE = "nurse"
    ADMIN = "admin"


@dataclass(frozen=True)
class User:
    id: int
    username: str
    password_hash: str
    full_name: str
    role: Role
    specialization: str | None
    is_active: bool