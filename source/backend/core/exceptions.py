"""Custom exceptions and the handlers that turn them into clean JSON errors."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mysql.connector import Error as MySQLError


class AppError(Exception):
    """Base class for expected, user-facing errors."""

    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AuthError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class AppointmentConflictError(ConflictError):
    """Raised when a doctor already has an active appointment at the requested time."""


class BookingClosedError(AppError):
    """Raised when online booking is switched off in the clinic settings."""

    status_code = 403


class TooManyRequestsError(AppError):
    status_code = 429


class ServiceUnavailableError(AppError):
    status_code = 503


def register_exception_handlers(app: FastAPI) -> None:
    """Attach handlers so errors never leak SQL, stack traces, or internals."""

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(MySQLError)
    async def handle_db_error(_: Request, __: MySQLError) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": "A database error occurred. Please try again."})