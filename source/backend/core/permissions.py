"""Shared access rules."""

from backend.core.exceptions import ForbiddenError


def doctor_scope(user: dict) -> int:
    """The doctor whose data this user may work with.

    A doctor works with their own data. A nurse works with the data of the
    doctor they are assigned to.
    """
    if user["role"] == "doctor":
        return user["id"]
    if user["role"] == "nurse" and user.get("assigned_doctor_id"):
        return user["assigned_doctor_id"]
    raise ForbiddenError("No doctor is assigned to your account. Ask an administrator.")