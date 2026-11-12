"""Every email AppointMed sends, one method per event.

Services call these after their transaction has committed, so a mail problem cannot undo saved work.
Routine notification failures are logged; the test-email check propagates delivery failures.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable, Sequence

from backend.core.config import Settings, settings
from backend.core.database import Database, database
from backend.core.email_templates import Button, render_email
from backend.core.mailer import Mailer, mailer
from backend.repositories.system_repository import PREF_KEYS, EmailPreferenceRepository, SettingsRepository

logger = logging.getLogger("appointmed")

CATEGORY_LABELS = {
    "notify_requests": "New appointment requests",
    "notify_appointments": "Appointment changes",
    "notify_billing": "Billing",
    "notify_account": "My account and schedule",
    "notify_clinic": "Clinic and system changes",
}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

SETTINGS_HINT = (
    "You are receiving this because of your email notification settings. "
    "You can change them in the app under Settings > Notifications."
)
SECURITY_HINT = "This is a security notice about your account, so it is always sent."
PATIENT_HINT = "This is an automated message. Please do not reply. If you need help, call the clinic."


def _when(value: datetime | str | None) -> str:
    if value is None:
        return "Not specified"
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return f"{value:%A, %B %d, %Y at %I:%M %p}"


def _day(value: date) -> str:
    return f"{value:%A, %B %d, %Y}"


def _money(value: Any) -> str:
    return f"PHP {Decimal(str(value)):,.2f}"


class Notifier:
    """Build and send the clinic's emails."""

    def __init__(self, db: Database = database, mail: Mailer = mailer, config: Settings = settings) -> None:
        self._db = db
        self._mail = mail
        self._config = config

    def _clinic(self) -> str:
        try:
            return SettingsRepository(self._db).as_dict().get("clinic_name") or "AppointMed"
        except Exception:
            logger.exception("Could not load the clinic name for an email.")
            return "AppointMed"

    def _url(self, path: str) -> str:
        return f"{self._config.app_url}{path}"

    def _staff(
        self,
        category: str | None,
        ids: Iterable[int | None],
        subject: str,
        *,
        exclude: int | None = None,
        include_inactive: bool = False,
        path: str | None = None,
        button_label: str | None = None,
        **content: Any,
    ) -> None:
        """Email staff members. `path` may contain {role}, filled in per person."""
        try:
            wanted = [user_id for user_id in dict.fromkeys(ids) if user_id is not None and user_id != exclude]
            people = EmailPreferenceRepository(self._db).recipients(
                wanted, category, active_only=not include_inactive
            )
            if not people:
                return
            clinic = self._clinic()
            footer = SETTINGS_HINT if category else SECURITY_HINT
            for person in people:
                button = Button(button_label, self._url(path.format(role=person["role"]))) if path and button_label else None
                text, html = render_email(
                    clinic=clinic,
                    greeting=f"Hello {person['full_name']},",
                    button=button,
                    footer=footer,
                    **content,
                )
                self._mail.send(person["email"], subject, text, html)
        except Exception:
            logger.exception("Could not send the '%s' email.", subject)

    def _direct(
        self,
        to: str | None,
        subject: str,
        *,
        name: str,
        footer: str = PATIENT_HINT,
        path: str | None = None,
        button_label: str | None = None,
        blocking: bool = False,
        **content: Any,
    ) -> None:
        """Email one address (a patient, or a test message)."""
        try:
            if not to:
                return
            button = Button(button_label, self._url(path)) if path and button_label else None
            text, html = render_email(
                clinic=self._clinic(), greeting=f"Hello {name},", button=button, footer=footer, **content
            )
            if blocking and self._config.smtp_enabled:
                self._mail.send_blocking(to, subject, text, html)
            else:
                self._mail.send(to, subject, text, html)
        except Exception:
            if blocking:
                raise
            logger.exception("Could not send the '%s' email.", subject)

    def _team(self, doctor_id: int) -> list[int]:
        try:
            return EmailPreferenceRepository(self._db).team_ids(doctor_id)
        except Exception:
            logger.exception("Could not find the recipients for doctor %s.", doctor_id)
            return []

    # ------------------------------------------------------------ patients
    def request_received(self, *, email: str | None, name: str, doctor_name: str, when: datetime) -> None:
        self._direct(
            email,
            "We received your appointment request",
            name=name,
            badge="Request received",
            tone="blue",
            heading="Your request is in",
            paragraphs=[
                "Thank you for booking with us. Our staff will review your request and email you as soon as it is confirmed.",
                "This is not a confirmed appointment yet.",
            ],
            details=[("Doctor", doctor_name), ("Requested time", _when(when))],
        )

    def request_approved(
        self, *, email: str | None, name: str, doctor_name: str, when: datetime, room_name: str | None
    ) -> None:
        details = [("Doctor", doctor_name), ("Date and time", _when(when))]
        if room_name:
            details.append(("Room", room_name))
        self._direct(
            email,
            "Your appointment is confirmed",
            name=name,
            badge="Confirmed",
            tone="green",
            heading="Your appointment is confirmed",
            paragraphs=["We look forward to seeing you. Please arrive a few minutes early so we can check you in."],
            details=details,
        )

    def request_dismissed(self, *, email: str | None, name: str, reason: str) -> None:
        self._direct(
            email,
            "About your appointment request",
            name=name,
            badge="Not confirmed",
            tone="amber",
            heading="We could not confirm your request",
            paragraphs=["Sorry, we were not able to confirm the time you asked for. You are welcome to request another time."],
            note=f"Reason: {reason}",
            path="/book",
            button_label="Request another time",
        )

    # ------------------------------------------------------------ staff: requests and appointments
    def new_request(
        self, *, doctor_id: int, nurse_id: int | None, requester: str, doctor_name: str, when: datetime
    ) -> None:
        self._staff(
            "notify_requests",
            [doctor_id, nurse_id],
            f"New appointment request from {requester}",
            badge="Needs your decision",
            tone="amber",
            heading="New appointment request",
            paragraphs=[
                "A patient asked for an appointment on the booking page. Please approve or disapprove it so they get a reply. "
                "Open the app to see their details."
            ],
            details=[("Patient", requester), ("Doctor", doctor_name), ("Requested time", _when(when))],
            path="/{role}/notifications",
            button_label="Review request",
        )

    def request_decided(
        self,
        *,
        actor_id: int,
        actor_name: str,
        doctor_id: int,
        patient: str,
        approved: bool,
        when: datetime | str | None,
        note: str | None,
    ) -> None:
        details = [("Patient", patient), ("Decided by", actor_name), ("Requested time", _when(when))]
        self._staff(
            "notify_requests",
            self._team(doctor_id),
            f"Request from {patient} was {'approved' if approved else 'disapproved'}",
            exclude=actor_id,
            badge="Approved" if approved else "Disapproved",
            tone="green" if approved else "red",
            heading="An appointment request was handled",
            paragraphs=[
                f"{actor_name} {'approved' if approved else 'disapproved'} a request, so there is nothing more to do for it."
            ],
            details=details,
            note=f"Reason given: {note}" if note else None,
            path="/{role}/appointments" if approved else "/{role}/notifications",
            button_label="Open the app",
        )

    def patient_checked_in(
        self, *, actor_id: int, actor_name: str, doctor_id: int, patient: str, room: str | None
    ) -> None:
        self._staff(
            "notify_appointments",
            [doctor_id],
            f"{patient} has checked in",
            exclude=actor_id,
            badge="Waiting",
            tone="blue",
            heading="A patient is waiting",
            paragraphs=[f"{actor_name} checked in a patient. They are in your waiting queue."],
            details=[("Patient", patient), ("Room", room or "No room chosen")],
            path="/{role}/appointments",
            button_label="Open appointments",
        )

    def appointment_cancelled(
        self, *, actor_id: int, actor_name: str, doctor_id: int, patient: str, when: datetime, reason: str | None
    ) -> None:
        self._staff(
            "notify_appointments",
            self._team(doctor_id),
            f"Appointment cancelled: {patient}",
            exclude=actor_id,
            badge="Cancelled",
            tone="red",
            heading="An appointment was cancelled",
            paragraphs=[f"{actor_name} cancelled an appointment. The time is free to book again."],
            details=[("Patient", patient), ("Was scheduled", _when(when)), ("Cancelled by", actor_name)],
            note=f"Reason: {reason}" if reason else None,
            path="/{role}/appointments",
            button_label="Open appointments",
        )

    def appointment_rescheduled(
        self, *, actor_id: int, actor_name: str, doctor_id: int, patient: str, old: datetime, new: datetime
    ) -> None:
        self._staff(
            "notify_appointments",
            self._team(doctor_id),
            f"Appointment moved: {patient}",
            exclude=actor_id,
            badge="Rescheduled",
            tone="blue",
            heading="An appointment was moved",
            paragraphs=[f"{actor_name} moved an appointment to a new time."],
            details=[("Patient", patient), ("Old time", _when(old)), ("New time", _when(new))],
            path="/{role}/appointments",
            button_label="Open appointments",
        )

    def day_off_changed(
        self, *, actor_id: int, doctor_id: int, doctor_name: str, day: date, reason: str | None, unavailable: bool
    ) -> None:
        self._staff(
            "notify_appointments",
            self._team(doctor_id),
            f"{doctor_name} is {'unavailable' if unavailable else 'available'} on {day:%b %d}",
            exclude=actor_id,
            badge="Not available" if unavailable else "Available again",
            tone="amber" if unavailable else "green",
            heading="A day off was marked" if unavailable else "A day off was removed",
            paragraphs=[
                f"{doctor_name} marked a day as unavailable. Patients can no longer book it online."
                if unavailable
                else f"{doctor_name} made a day available again. Patients can book it online."
            ],
            details=[("Doctor", doctor_name), ("Date", _day(day))] + ([("Reason", reason)] if reason else []),
            path="/{role}/appointments",
            button_label="Open appointments",
        )

    # ------------------------------------------------------------ staff: billing
    def awaiting_payment(self, *, actor_id: int, actor_name: str, doctor_id: int, patient: str, amount: Any) -> None:
        self._staff(
            "notify_billing",
            self._team(doctor_id),
            f"{patient} is ready to pay",
            exclude=actor_id,
            badge="Awaiting payment",
            tone="amber",
            heading="An examination is finished",
            paragraphs=[f"{actor_name} finished an examination. The invoice is ready, and the patient can pay now."],
            details=[("Patient", patient), ("Total", _money(amount))],
            path="/{role}/invoice",
            button_label="Open invoices",
        )

    def payment_received(self, *, actor_id: int, actor_name: str, doctor_id: int, patient: str, amount: Any) -> None:
        self._staff(
            "notify_billing",
            self._team(doctor_id),
            f"Payment received from {patient}",
            exclude=actor_id,
            badge="Paid",
            tone="green",
            heading="A payment was recorded",
            paragraphs=[f"{actor_name} marked an invoice as paid. The visit is now in History."],
            details=[("Patient", patient), ("Amount", _money(amount)), ("Received by", actor_name)],
            path="/{role}/invoice",
            button_label="Open invoices",
        )

    # ------------------------------------------------------------ staff: accounts (admin actions)
    def account_created(self, *, user_id: int, username: str, role: str, by_name: str) -> None:
        self._staff(
            None,
            [user_id],
            "Your AppointMed account is ready",
            badge="Welcome",
            tone="green",
            heading="You were added to the clinic",
            paragraphs=[
                f"{by_name} created your account. Your administrator will give you your password separately. "
                "After your first sign-in, change it under Settings."
            ],
            details=[("Username", username), ("Role", role.title())],
            path="/staff-login",
            button_label="Go to staff sign-in",
        )

    def nurse_assignment(self, *, doctor_id: int, nurse_name: str, assigned: bool, by_name: str) -> None:
        self._staff(
            "notify_account",
            [doctor_id],
            f"{nurse_name} {'now supports you' if assigned else 'no longer supports you'}",
            badge="Team change",
            tone="blue",
            heading="Your nursing team changed",
            paragraphs=[
                f"{by_name} {'assigned' if assigned else 'removed'} a nurse "
                f"{'to' if assigned else 'from'} your team."
            ],
            details=[("Nurse", nurse_name), ("Change", "Added to your team" if assigned else "Removed from your team")],
            path="/{role}/dashboard",
            button_label="Open the app",
        )

    def account_updated(
        self, *, user_id: int, by_name: str, changes: Sequence[tuple[str, str]]
    ) -> None:
        self._staff(
            "notify_account",
            [user_id],
            "Your account details were updated",
            badge="Account updated",
            tone="blue",
            heading="Your details were changed",
            paragraphs=[f"{by_name} updated your account. These are the new values."],
            details=list(changes),
            note="If this is not what you expected, please contact an administrator.",
            path="/{role}/profile",
            button_label="Open your profile",
        )

    def account_status(self, *, user_id: int, active: bool, by_name: str) -> None:
        if active:
            self._staff(
                None,
                [user_id],
                "Your AppointMed account was reactivated",
                include_inactive=True,
                badge="Reactivated",
                tone="green",
                heading="Welcome back",
                paragraphs=[f"{by_name} reactivated your account. You can sign in again."],
                path="/staff-login",
                button_label="Go to staff sign-in",
            )
        else:
            self._staff(
                None,
                [user_id],
                "Your AppointMed account was deactivated",
                include_inactive=True,
                badge="Deactivated",
                tone="red",
                heading="Your account was deactivated",
                paragraphs=[
                    f"{by_name} deactivated your account, so you can no longer sign in. "
                    "Your records and history are kept."
                ],
                note="If you think this is a mistake, please contact an administrator.",
            )

    def password_reset(self, *, user_id: int, by_name: str) -> None:
        self._staff(
            None,
            [user_id],
            "Your password was reset",
            badge="Password reset",
            tone="amber",
            heading="An administrator reset your password",
            paragraphs=[
                f"{by_name} set a new password for your account. They will share it with you directly. "
                "Please change it after you sign in."
            ],
            note="If you did not expect this, contact an administrator.",
            path="/staff-login",
            button_label="Go to staff sign-in",
        )

    def password_changed(self, user_id: int) -> None:
        self._staff(
            None,
            [user_id],
            "Your password was changed",
            badge="Security",
            tone="green",
            heading="Your password was changed",
            paragraphs=["You changed your password from the Settings page."],
            note="If this was not you, contact an administrator immediately.",
        )

    def schedule_updated(self, *, doctor_id: int, actor_name: str, blocks: Sequence[Any]) -> None:
        by_day: dict[int, list[str]] = {}
        for block in blocks:
            by_day.setdefault(block.weekday, []).append(f"{block.start_time:%H:%M} - {block.end_time:%H:%M}")
        details = [(WEEKDAYS[weekday - 1], ", ".join(by_day[weekday]) if weekday in by_day else "Not working") for weekday in range(1, 8)]
        self._staff(
            "notify_account",
            [doctor_id],
            "Your working hours were updated",
            badge="Schedule updated",
            tone="blue",
            heading="Your weekly schedule changed",
            paragraphs=[
                f"{actor_name} updated your working hours. This is your schedule now. "
                "Patients can only book inside these times."
            ],
            details=details,
            path="/{role}/appointments",
            button_label="Open appointments",
        )

    # ------------------------------------------------------------ staff: clinic and system
    def clinic_changed(
        self, *, actor_id: int, actor_name: str, title: str, lines: Sequence[tuple[str, str]]
    ) -> None:
        try:
            everyone = EmailPreferenceRepository(self._db).staff_ids(("doctor", "nurse", "admin"))
        except Exception:
            logger.exception("Could not find staff recipients for a clinic update.")
            return
        self._staff(
            "notify_clinic",
            everyone,
            title,
            exclude=actor_id,
            badge="Clinic update",
            tone="blue",
            heading=title,
            paragraphs=[f"{actor_name} made the following change."],
            details=list(lines),
            path="/{role}/dashboard",
            button_label="Open the app",
        )

    def database_event(self, *, actor_id: int, actor_name: str, title: str, detail: str) -> None:
        try:
            admins = EmailPreferenceRepository(self._db).staff_ids(("admin",))
        except Exception:
            logger.exception("Could not find admin recipients for a database event.")
            return
        self._staff(
            "notify_clinic",
            admins,
            title,
            exclude=actor_id,
            badge="System notice",
            tone="amber",
            heading=title,
            paragraphs=[f"{actor_name} did this from the Database page."],
            details=[("Who", actor_name), ("Details", detail)],
            note="If you did not expect this, review the audit log.",
            path="/admin/audits",
            button_label="Open audit logs",
        )

    # ------------------------------------------------------------ settings test
    def test_email(self, *, to: str, name: str, prefs: dict[str, bool]) -> None:
        self._direct(
            to,
            "AppointMed test email",
            name=name,
            footer="You asked for this test from Settings > Notifications.",
            badge="Test email",
            tone="green",
            blocking=True,
            heading="Email notifications are working",
            paragraphs=[
                "This is a test message. If you can read it, AppointMed can reach you. These are your current settings."
            ],
            details=[(CATEGORY_LABELS[key], "On" if prefs.get(key, True) else "Off") for key in PREF_KEYS],
            note="Security emails (new account, password changes, deactivation) are always sent.",
        )


notifier = Notifier()
