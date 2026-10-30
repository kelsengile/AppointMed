"""Outgoing email. Sends through SMTP when configured, otherwise writes the email to the log."""

from __future__ import annotations

import logging
import smtplib
import ssl
import threading
from email.message import EmailMessage

from .config import Settings, settings

logger = logging.getLogger("appointmed")


class Mailer:
    """Sends short plain-text emails without blocking the request."""

    def __init__(self, config: Settings = settings) -> None:
        self._config = config

    def send(self, to: str | None, subject: str, body: str) -> None:
        """Queue an email in a background thread. Silently skips when there is no address."""
        if not to:
            return
        threading.Thread(target=self._safe_deliver, args=(to, subject, body), daemon=True).start()

    def send_blocking(self, to: str, subject: str, body: str) -> None:
        """Send right now and raise on failure. Used by test_email.py to check the SMTP settings."""
        if not self._config.smtp_enabled:
            raise RuntimeError("SMTP_HOST is empty in source/.env, so no real email can be sent.")
        self._deliver(to, subject, body)

    def _safe_deliver(self, to: str, subject: str, body: str) -> None:
        """Background version: failures are logged and never break the request."""
        if not self._config.smtp_enabled:
            logger.info("EMAIL (SMTP not configured, not sent)\nTo: %s\nSubject: %s\n\n%s", to, subject, body)
            return
        try:
            self._deliver(to, subject, body)
        except smtplib.SMTPAuthenticationError:
            logger.error("Email to %s failed: the SMTP username or password was rejected. Check SMTP_USER and SMTP_PASSWORD.", to)
        except smtplib.SMTPRecipientsRefused:
            logger.error("Email failed: the address %s was refused by the mail server.", to)
        except smtplib.SMTPSenderRefused:
            logger.error("Email to %s failed: the server refused SMTP_FROM (%s). Use your own address.", to, self._config.smtp_from)
        except (smtplib.SMTPException, OSError, ssl.SSLError) as exc:
            logger.error("Could not send email to %s: %s", to, exc)

    def _deliver(self, to: str, subject: str, body: str) -> None:
        cfg = self._config
        message = EmailMessage()
        message["From"] = cfg.smtp_from
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        context = ssl.create_default_context()
        if cfg.smtp_port == 465:  # implicit SSL (the connection is encrypted from the start)
            server: smtplib.SMTP = smtplib.SMTP_SSL(cfg.smtp_host, cfg.smtp_port, timeout=20, context=context)
        else:  # plain connection, upgraded with STARTTLS (usually port 587)
            server = smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=20)
        with server:
            server.ehlo()
            if cfg.smtp_port != 465 and cfg.smtp_tls:
                server.starttls(context=context)
                server.ehlo()
            if cfg.smtp_user:
                server.login(cfg.smtp_user, cfg.smtp_password)
            server.send_message(message)
        logger.info("Email sent to %s (%s)", to, subject)


mailer = Mailer()