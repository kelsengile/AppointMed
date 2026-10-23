"""Outgoing email. Sends through SMTP when configured, otherwise writes the email to the log."""

from __future__ import annotations

import logging
import smtplib
import threading
from email.message import EmailMessage

from .config import Settings, settings

logger = logging.getLogger("appointmed")


class Mailer:
    """Sends short plain-text emails without blocking the request."""

    def __init__(self, config: Settings = settings) -> None:
        self._config = config

    def send(self, to: str | None, subject: str, body: str) -> None:
        """Queue an email. Silently skips when there is no address."""
        if not to:
            return
        threading.Thread(target=self._deliver, args=(to, subject, body), daemon=True).start()

    def _deliver(self, to: str, subject: str, body: str) -> None:
        """Do the actual sending. Failures are logged and never break the request."""
        if not self._config.smtp_enabled:
            logger.info("EMAIL (SMTP not configured, not sent)\nTo: %s\nSubject: %s\n\n%s", to, subject, body)
            return
        message = EmailMessage()
        message["From"] = self._config.smtp_from
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        try:
            with smtplib.SMTP(self._config.smtp_host, self._config.smtp_port, timeout=10) as server:
                if self._config.smtp_tls:
                    server.starttls()
                if self._config.smtp_user:
                    server.login(self._config.smtp_user, self._config.smtp_password)
                server.send_message(message)
        except (smtplib.SMTPException, OSError) as exc:
            logger.error("Could not send email to %s: %s", to, exc)


mailer = Mailer()