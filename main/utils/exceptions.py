"""
Custom exceptions for AppointMed.

Instead of letting normal Python errors show confusing messages to the
user, we raise one of these instead. Each type of problem gets its own
class, so the code that catches them knows exactly what went wrong.
"""


class AppointMedError(Exception):
    """Base class for all of our own custom errors. Every error below
    is a kind of AppointMedError, so the views can catch just this one
    class and still handle every case."""
    pass


class InvalidCredentialsError(AppointMedError):
    """Raised when the username or password typed on login is wrong."""
    pass


class DoubleBookingError(AppointMedError):
    """Raised when a doctor already has an appointment at that time."""
    pass


class InvalidAppointmentTimeError(AppointMedError):
    """Raised when an appointment is scheduled in the past."""
    pass


class EmptyFieldError(AppointMedError):
    """Raised when a required form field was left blank."""
    pass


class RecordNotFoundError(AppointMedError):
    """Raised when trying to update or delete a record that does not exist."""
    pass


class DatabaseConnectionError(AppointMedError):
    """Raised when the app cannot reach the database server."""
    pass
