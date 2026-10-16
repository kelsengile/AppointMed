"""Custom exceptions. Each one carries the HTTP status it maps to."""


class AppError(Exception):
    """Base class for all expected application errors."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ServerConnectionError(AppError):
    """The MySQL server rejected or could not be reached with the given details."""

    status_code = 400


class ServerNotConnectedError(AppError):
    """An action needs the database but no server connection has been made yet."""

    status_code = 503

    def __init__(self, message: str = "Not connected to a database server. Connect from the login screen first.") -> None:
        super().__init__(message)


class AuthenticationError(AppError):
    status_code = 401


class InactiveAccountError(AppError):
    status_code = 403


class PermissionDeniedError(AppError):
    status_code = 403


class ConfigurationError(AppError):
    status_code = 500