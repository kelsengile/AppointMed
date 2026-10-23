"""Application settings, read from environment variables (source/.env)."""

import os
from pathlib import Path

from dotenv import load_dotenv

APP_NAME = "AppointMed"
APP_VERSION = "0.2.0"

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def _flag(name: str, default: bool) -> bool:
    """Read a true/false environment variable."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    """Holds every configuration value the backend needs."""

    def __init__(self) -> None:
        self.app_env = os.getenv("APP_ENV", "development")

        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = int(os.getenv("DB_PORT", "3306"))
        self.db_name = os.getenv("DB_NAME", "appointmed")
        self.db_user = os.getenv("DB_USER", "appointmed_user")
        self.db_password = os.getenv("DB_PASSWORD", "")

        origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
        self.cors_origins = [o.strip() for o in origins.split(",") if o.strip()]
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")

        self.jwt_secret = os.getenv("JWT_SECRET", "")
        self.jwt_expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

        # Email. With no SMTP_HOST the mailer prints messages to the terminal instead.
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from = os.getenv("SMTP_FROM", "AppointMed <no-reply@example.com>")
        self.smtp_use_tls = _flag("SMTP_USE_TLS", True)


settings = Settings()