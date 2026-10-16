"""FastAPI application for AppointMed."""
import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# main/.env (this file lives in main/backend)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from backend.core.exception_handlers import register_exception_handlers  # noqa: E402
from backend.routes.auth_routes import router as auth_router  # noqa: E402
from backend.routes.server_routes import router as server_router  # noqa: E402

DEFAULT_ORIGINS = (
    "http://127.0.0.1:5173,http://localhost:5173,"
    "http://127.0.0.1:5174,http://localhost:5174"
)

app = FastAPI(title="AppointMed API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", DEFAULT_ORIGINS).split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(server_router)
app.include_router(auth_router)


@app.get("/health")
def health() -> dict:
    """Confirms the API is running."""
    return {"status": "ok", "service": "AppointMed API"}


@app.get("/health/db")
def health_db() -> dict:
    """Confirms the API can reach MySQL (uses the .env credentials)."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", ""),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "appointmed"),
            connection_timeout=3,
        )
        connection.close()
        return {"status": "ok"}
    except mysql.connector.Error:
        # Do not leak connection details to the client.
        return {"status": "error", "detail": "Cannot connect to the database."}