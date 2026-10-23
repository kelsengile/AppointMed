"""Application settings, read once from the environment (source/.env)."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

APP_NAME = "AppointMed"
APP_VERSION = "1.0.0"

# source/backend/core/config.py -> parents[2] is the `source` folder.
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_FILE)

logger = logging.getLogger("appointmed")


def _split(value: str) -> list[str]:
    """Turn 'a, b, c' into ['a', 'b', 'c'], ignoring blanks."""
    return [part.strip() for part in value.split(",") if part.strip()]


@dataclass(frozen=True)
class Settings:
    """Immutable bag of configuration values (encapsulates reading the environment)."""

    app_env: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    jwt_secret: str
    jwt_expire_minutes: int
    cors_origins: list[str]
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_from: str
    smtp_tls: bool

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from environment variables, applying safe defaults."""
        secret = os.getenv("JWT_SECRET", "").strip()
        if not secret:
            raise RuntimeError("JWT_SECRET is missing. Set it in source/.env (see CONTRIBUTING.md, Step 6).")
        if secret == "change_this_secret":
            logger.warning("JWT_SECRET is still the placeholder. Generate a real one before sharing this app.")
        return cls(
            app_env=os.getenv("APP_ENV", "development"),
            db_host=os.getenv("DB_HOST", "localhost"),
            db_port=int(os.getenv("DB_PORT", "3306")),
            db_name=os.getenv("DB_NAME", "appointmed"),
            db_user=os.getenv("DB_USER", "appointmed_user"),
            db_password=os.getenv("DB_PASSWORD", ""),
            jwt_secret=secret,
            jwt_expire_minutes=int(os.getenv("JWT_EXPIRE_MINUTES", "480")),
            cors_origins=_split(os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")),
            smtp_host=os.getenv("SMTP_HOST", "").strip(),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_user=os.getenv("SMTP_USER", "").strip(),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            smtp_from=os.getenv("SMTP_FROM", "no-reply@appointmed.example"),
            smtp_tls=os.getenv("SMTP_TLS", "true").lower() == "true",
        )

    @property
    def smtp_enabled(self) -> bool:
        """True when an SMTP server is configured, so real emails can be sent."""
        return bool(self.smtp_host)


settings = Settings.from_env()