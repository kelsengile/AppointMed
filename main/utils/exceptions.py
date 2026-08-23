"""
Custom exceptions for AppointMed.
Satisfies the "minimum of one custom exception" requirement, with room
to grow — each error case gets its own class so callers can catch
precisely and the GUI layer can show a friendly message per case.
"""


class AppointMedError(Exception):
    """Base class for all application-specific errors."""
    pass


class InvalidCredentialsError(AppointMedError):
    """Raised when login username/password is incorrect."""
    pass


class DoubleBookingError(AppointMedError):
    """Raised when an appointment slot is already taken for a doctor."""
    pass


class InvalidAppointmentTimeError(AppointMedError):
    """Raised when an appointment is scheduled outside clinic hours
    or in the past."""
    pass


class EmptyFieldError(AppointMedError):
    """Raised when a required form field is left blank."""
    pass


class RecordNotFoundError(AppointMedError):
    """Raised when a search/edit/delete targets a record that doesn't exist."""
    pass


class DatabaseConnectionError(AppointMedError):
    """Raised when the app cannot reach the central database server."""
    pass
