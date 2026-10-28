"""Custom exceptions and the handlers that turn them into clean JSON errors.

Every business problem raises a subclass of AppError. The handler below converts it into
{"detail": "<plain message>"} with the right HTTP status, so the frontend can show it as is.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("appointmed")


class AppError(Exception):
    """Base class for all expected errors. Carries an HTTP status and a user-safe message."""

    status_code = 400
    default_message = "The request could not be completed."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class ValidationFailedError(AppError):
    """Input is well-formed but breaks a business rule."""

    status_code = 400


class AuthenticationError(AppError):
    """The user is not signed in or the credentials are wrong."""

    status_code = 401
    default_message = "Please sign in."


class PermissionDeniedError(AppError):
    """The signed-in user is not allowed to do this."""

    status_code = 403
    default_message = "You do not have permission to do that."


class NotFoundError(AppError):
    """The requested record does not exist (or is outside the user's scope)."""

    status_code = 404
    default_message = "Record not found."


class ConflictError(AppError):
    """The change clashes with the current state of the data."""

    status_code = 409
    default_message = "That change conflicts with existing data."


class DuplicateEntryError(ConflictError):
    """A unique value (such as a username) already exists."""

    default_message = "That record already exists."


class AppointmentConflictError(ConflictError):
    """Raised when a doctor already has an active appointment at the requested time."""

    default_message = "That time is already booked for this doctor."


class InvalidScheduleError(AppError):
    """The requested time is outside the doctor's schedule or booking window."""

    status_code = 400
    default_message = "That time is not available."


class InvalidStatusError(ConflictError):
    """An appointment status change that the workflow does not allow."""

    default_message = "That action is not allowed in the appointment's current status."


class RateLimitError(AppError):
    """Too many attempts in a short time."""

    status_code = 429
    default_message = "Too many attempts. Please wait a few minutes and try again."


class DatabaseUnavailableError(AppError):
    """MySQL could not be reached or failed. Never exposes SQL or driver details."""

    status_code = 503
    default_message = "The database is not available right now. Please try again."


def register_exception_handlers(app: FastAPI) -> None:
    """Attach handlers so every error leaves the API as {"detail": "..."}."""

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        parts: list[str] = []
        for error in exc.errors():
            location = ".".join(str(p) for p in error.get("loc", ()) if p not in ("body", "query", "path"))
            message = str(error.get("msg", "Invalid value")).removeprefix("Value error, ")
            parts.append(f"{location}: {message}" if location else message)
        return JSONResponse(status_code=422, content={"detail": "; ".join(parts) or "Invalid input."})

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Something went wrong on the server. Please try again."})