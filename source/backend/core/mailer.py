"""Outgoing email. Sends through SMTP when configured, otherwise writes the email to the log.

Messages carry a plain-text body and, when given, an HTML version (mail apps show the HTML one).
"""

from __future__ import annotations

import logging
import smtplib
import socket
import ssl
import threading
from email.message import EmailMessage
from pathlib import Path

from .config import Settings, settings
from .email_templates import LOGO_CID

logger = logging.getLogger("appointmed")

LOGO_PATH = Path(__file__).resolve().parents[2] / "assets" / "icons" / "appointmed-logo-email.png"
PLACEHOLDER_FROM = "no-reply@appointmed.example"
TIMEOUT = 20


class Mailer:
    """Sends emails without blocking the request."""

    def __init__(self, config: Settings = settings) -> None:
        self._config = config

    # ------------------------------------------------------------ public
    def send(self, to: str | None, subject: str, body: str, html: str | None = None) -> None:
        """Queue an email in a background thread. Silently skips when there is no address."""
        if not to:
            return
        threading.Thread(target=self._safe_deliver, args=(to, subject, body, html), daemon=True).start()

    def send_blocking(self, to: str, subject: str, body: str, html: str | None = None) -> None:
        if not self._config.smtp_enabled:
            raise RuntimeError("SMTP_HOST is empty in source/.env, so no real email can be sent.")
        if self._config.smtp_user and not self._config.smtp_password:
            raise RuntimeError("SMTP_USER is set but SMTP_PASSWORD is empty in source/.env.")
        self._deliver(to, subject, body, html)

    # ------------------------------------------------------------ helpers
    def _sender(self) -> str:
        """Gmail and most providers only accept their own account as the sender."""
        cfg = self._config
        if cfg.smtp_user and (not cfg.smtp_from or cfg.smtp_from == PLACEHOLDER_FROM):
            return cfg.smtp_user
        return cfg.smtp_from

    def _password(self) -> str:
        """Gmail shows app passwords in groups with spaces; the spaces are not part of the password."""
        password = self._config.smtp_password
        if "gmail" in self._config.smtp_host.lower() or "googlemail" in self._config.smtp_host.lower():
            return password.replace(" ", "")
        return password

    def _build(self, to: str, subject: str, body: str, html: str | None) -> EmailMessage:
        message = EmailMessage()
        message["From"] = self._sender()
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        if html:
            message.add_alternative(html, subtype="html")
            if LOGO_PATH.is_file() and LOGO_PATH.stat().st_size <= 200_000:
                message.get_body(("html",)).add_related(
                    LOGO_PATH.read_bytes(),
                    maintype="image",
                    subtype="png",
                    cid=f"<{LOGO_CID}>",
                    filename="appointmed-logo.png",
                    disposition="inline",
                )
            else:
                logger.warning(
                    "Email logo missing or over 200 KB at %s, the header icon will be skipped.", LOGO_PATH
                )
        return message

    def _send_once(self, message: EmailMessage, port: int, use_ssl: bool) -> None:
        """One complete attempt: connect, (STARTTLS), log in, send, quit."""
        cfg = self._config
        context = ssl.create_default_context()
        if use_ssl:  # implicit SSL (port 465): encrypted from the first byte
            server: smtplib.SMTP = smtplib.SMTP_SSL(cfg.smtp_host, port, timeout=TIMEOUT, context=context)
        else:  # plain connection, upgraded with STARTTLS (usually port 587)
            server = smtplib.SMTP(cfg.smtp_host, port, timeout=TIMEOUT)
        try:
            server.ehlo()
            if not use_ssl and cfg.smtp_tls:
                if not server.has_extn("starttls"):
                    raise smtplib.SMTPNotSupportedError("The server does not offer STARTTLS on this port.")
                server.starttls(context=context)
                server.ehlo()
            if cfg.smtp_user:
                server.login(cfg.smtp_user, self._password())
            server.send_message(message)
        finally:
            try:
                server.quit()
            except (smtplib.SMTPException, OSError):
                server.close()

    def _deliver(self, to: str, subject: str, body: str, html: str | None) -> None:
        cfg = self._config
        message = self._build(to, subject, body, html)

        attempts = [(cfg.smtp_port, cfg.smtp_port == 465)]
        # If the server hangs up, the port/TLS pairing is probably wrong: also try the other standard one.
        if cfg.smtp_port == 587:
            attempts.append((465, True))
        elif cfg.smtp_port == 465:
            attempts.append((587, False))

        last: Exception | None = None
        for port, use_ssl in attempts:
            try:
                self._send_once(message, port, use_ssl)
                if (port, use_ssl) != attempts[0]:
                    logger.warning(
                        "Email worked on port %s (%s) but not on SMTP_PORT=%s. Set SMTP_PORT=%s in source/.env.",
                        port, "SSL" if use_ssl else "STARTTLS", cfg.smtp_port, port,
                    )
                logger.info("Email sent to %s (%s)", to, subject)
                return
            except (smtplib.SMTPServerDisconnected, ssl.SSLError, socket.timeout, ConnectionError) as exc:
                last = exc  # try the next mode
            except smtplib.SMTPNotSupportedError as exc:
                last = exc
        assert last is not None
        raise last

    def _safe_deliver(self, to: str, subject: str, body: str, html: str | None) -> None:
        """Background version: failures are logged and never break the request."""
        cfg = self._config
        if not cfg.smtp_enabled:
            logger.info("EMAIL (SMTP not configured, not sent)\nTo: %s\nSubject: %s\n\n%s", to, subject, body)
            return
        try:
            self._deliver(to, subject, body, html)
        except smtplib.SMTPAuthenticationError:
            logger.error(
                "Email to %s failed: the SMTP username or password was rejected. "
                "For Gmail use a 16-character App Password (not your normal password).", to,
            )
        except smtplib.SMTPRecipientsRefused:
            logger.error("Email failed: the address %s was refused by the mail server.", to)
        except smtplib.SMTPSenderRefused:
            logger.error("Email to %s failed: the server refused the sender (%s). Set SMTP_FROM to your own address.", to, self._sender())
        except smtplib.SMTPServerDisconnected as exc:
            logger.error(
                "Email to %s failed: the mail server closed the connection (%s). Check SMTP_PORT (587 with SMTP_TLS=true, "
                "or 465), use an App Password for Gmail, and make sure your network does not block the port.", to, exc,
            )
        except (smtplib.SMTPException, OSError, ssl.SSLError) as exc:
            logger.error("Could not send email to %s: %s", to, exc)
        except Exception:
            logger.exception("Unexpected error while sending email to %s.", to)


mailer = Mailer()