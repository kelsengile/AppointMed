"""Sends email. Without SMTP settings, messages are printed to the backend terminal."""

import logging
import smtplib
import threading
from email.message import EmailMessage

from backend.core.config import Settings, settings

log = logging.getLogger("uvicorn.error")


class Mailer:
    """Sends plain-text email in a background thread so requests are never slowed down."""

    def __init__(self, config: Settings) -> None:
        self._config = config

    def send(self, to: str | None, subject: str, body: str) -> None:
        """Queue one email. Does nothing if there is no recipient."""
        if not to:
            return
        threading.Thread(target=self._deliver, args=(to, subject, body), daemon=True).start()

    def _deliver(self, to: str, subject: str, body: str) -> None:
        cfg = self._config
        if not cfg.smtp_host:
            log.info("[email not sent, SMTP_HOST is empty]\nTo: %s\nSubject: %s\n\n%s", to, subject, body)
            return
        message = EmailMessage()
        message["From"] = cfg.smtp_from
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        try:
            if cfg.smtp_port == 465:
                server: smtplib.SMTP = smtplib.SMTP_SSL(cfg.smtp_host, cfg.smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=10)
                if cfg.smtp_use_tls:
                    server.starttls()
            with server:
                if cfg.smtp_user:
                    server.login(cfg.smtp_user, cfg.smtp_password)
                server.send_message(message)
        except (smtplib.SMTPException, OSError):
            log.exception("Could not send email to %s", to)


mailer = Mailer(settings)