"""Endpoints for doctors and nurses. Role checks happen here, on the backend."""

from datetime import date

from fastapi import APIRouter, Depends, Query

from backend.core.deps import require_roles
from backend.schemas.clinic import DismissRequest, ExaminationFinish
from backend.services.booking_service import booking_service
from backend.services.visit_service import visit_service

router = APIRouter(prefix="/api", tags=["staff"])

clinical = Depends(require_roles("doctor", "nurse"))
nurse_only = Depends(require_roles("nurse"))
doctor_only = Depends(require_roles("doctor"))


# ---------- booking requests ----------

@router.get("/notifications")
def list_notifications(
    status: str = Query("Pending", pattern="^(Pending|Converted|Dismissed|all)$"),
    user: dict = clinical,
) -> list[dict]:
    return booking_service.list_notifications(user, status)


@router.post("/notifications/{notification_id}/approve")
def approve_notification(notification_id: int, user: dict = clinical) -> dict:
    return booking_service.approve(notification_id, user)


@router.post("/notifications/{notification_id}/dismiss")
def dismiss_notification(notification_id: int, body: DismissRequest, user: dict = clinical) -> dict:
    return booking_service.dismiss(notification_id, user, body.note)


# ---------- appointments ----------

@router.get("/appointments")
def appointments(day: date | None = Query(None, alias="date"), user: dict = clinical) -> list[dict]:
    return visit_service.board(user, day or date.today())


@router.post("/appointments/{appointment_id}/check-in")
def check_in(appointment_id: int, user: dict = nurse_only) -> dict:
    return visit_service.check_in(appointment_id, user)


@router.post("/appointments/{appointment_id}/cancel")
def cancel(appointment_id: int, user: dict = nurse_only) -> dict:
    return visit_service.cancel(appointment_id, user)


@router.post("/appointments/{appointment_id}/start")
def start_exam(appointment_id: int, user: dict = doctor_only) -> dict:
    return visit_service.start_exam(appointment_id, user)


@router.post("/appointments/{appointment_id}/finish")
def finish_exam(appointment_id: int, body: ExaminationFinish, user: dict = doctor_only) -> dict:
    return visit_service.finish_exam(appointment_id, user, body)


# ---------- invoices ----------

@router.get("/invoices")
def invoices(
    status: str = Query("Unpaid", pattern="^(Unpaid|Paid|all)$"),
    user: dict = clinical,
) -> list[dict]:
    return visit_service.invoices(user, status)


@router.post("/invoices/{invoice_id}/pay")
def pay_invoice(invoice_id: int, user: dict = clinical) -> dict:
    return visit_service.pay(invoice_id, user)


# ---------- history and patients ----------

@router.get("/history")
def history(search: str | None = None, patient_id: int | None = None, user: dict = clinical) -> list[dict]:
    return visit_service.history(user, search, patient_id)


@router.get("/patients")
def patients(search: str = "", user: dict = clinical) -> list[dict]:
    return visit_service.patients(user, search)