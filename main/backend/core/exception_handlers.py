"""Maps exceptions to clean JSON responses (no stack traces or SQL details)."""
import logging

import mysql.connector
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.exceptions.app_exceptions import AppError

logger = logging.getLogger("appointmed")


async def handle_app_error(_: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, AppError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
    return JSONResponse(status_code=500, content={"detail": "Unexpected error."})


async def handle_mysql_error(_: Request, exc: Exception) -> JSONResponse:
    logger.error("Database error: %s", exc)
    return JSONResponse(status_code=503, content={"detail": "A database error occurred."})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(mysql.connector.Error, handle_mysql_error)