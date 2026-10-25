"""Doctor and nurse endpoints. Every route checks the role's feature on the server."""

from datetime import date

from fastapi import APIRouter, Depends

from backend.core.security import require_feature
from backend.models.domain import User
from backend.schemas.api import (
    AppointmentCreate,
    ApproveRequest,
    CancelRequest,
    DismissRequest,
    ExamFinish,
    PatientIn,
    RescheduleRequest,
    RoomAssign,
    RoomStatusUpdate,
)
from backend.services.appointment_service import AppointmentService
from backend.services.billing_service import BillingService
from backend.services.dashboard_service import DashboardService
from backend.services.patient_service import PatientService

router = APIRouter(prefix="/api/staff", tags=["staff"])
appointment_service = AppointmentService()
billing_service = BillingService()
patient_service = PatientService()
dashboard_service = DashboardService()


# ---------- dashboard ----------
@router.get("/dashboard")
def dashboard(user: User = Depends(require_feature("dashboard"))) -> dict:
    return dashboard_service.staff(user)


# ---------- notifications ----------
@router.get("/notifications")
def notifications(status: str | None = None, user: User = Depends(require_feature("notifications"))) -> list:
    return appointment_service.list_notifications(user, status)


@router.post("/notifications/{notification_id}/approve")
def approve(notification_id: int, body: ApproveRequest, user: User = Depends(require_feature("notifications"))) -> dict:
    return appointment_service.approve_notification(user, notification_id, body.room_id, body.scheduled_time)


@router.post("/notifications/{notification_id}/dismiss")
def dismiss(notification_id: int, body: DismissRequest, user: User = Depends(require_feature("notifications"))) -> dict:
    appointment_service.dismiss_notification(user, notification_id, body.note)
    return {"ok": True}


# ---------- appointments ----------
@router.get("/appointments")
def appointments(day: str = "today", q: str | None = None, user: User = Depends(require_feature("appointments"))) -> list:
    return appointment_service.list_appointments(user, day, q)


@router.get("/calendar")
def calendar(date_from: date, date_to: date, user: User = Depends(require_feature("appointments"))) -> dict:
    return appointment_service.calendar(user, date_from, date_to)


@router.post("/appointments", status_code=201)
def create_appointment(body: AppointmentCreate, user: User = Depends(require_feature("appointments"))) -> dict:
    return appointment_service.create_appointment(user, body)


@router.post("/appointments/{appointment_id}/check-in")
def check_in(appointment_id: int, user: User = Depends(require_feature("appointments"))) -> dict:
    return appointment_service.check_in(user, appointment_id)


@router.post("/appointments/{appointment_id}/start")
def start_exam(appointment_id: int, body: RoomAssign, user: User = Depends(require_feature("exam"))) -> dict:
    return appointment_service.start_exam(user, appointment_id, body.room_id)


@router.post("/appointments/{appointment_id}/release")
def release(appointment_id: int, user: User = Depends(require_feature("exam"))) -> dict:
    return appointment_service.release(user, appointment_id)


@router.post("/appointments/{appointment_id}/finish")
def finish_exam(appointment_id: int, body: ExamFinish, user: User = Depends(require_feature("exam"))) -> dict:
    return appointment_service.finish_exam(user, appointment_id, body)


@router.post("/appointments/{appointment_id}/cancel")
def cancel(appointment_id: int, body: CancelRequest, user: User = Depends(require_feature("appointments"))) -> dict:
    return appointment_service.cancel(user, appointment_id, body.reason)


@router.post("/appointments/{appointment_id}/reschedule")
def reschedule(appointment_id: int, body: RescheduleRequest, user: User = Depends(require_feature("appointments"))) -> dict:
    return appointment_service.reschedule(user, appointment_id, body.scheduled_time)


@router.put("/appointments/{appointment_id}/room")
def assign_room(appointment_id: int, body: RoomAssign, user: User = Depends(require_feature("appointments"))) -> dict:
    return appointment_service.assign_room(user, appointment_id, body.room_id)


@router.post("/appointments/{appointment_id}/bill")
def bill(appointment_id: int, user: User = Depends(require_feature("invoice"))) -> dict:
    return billing_service.bill(user, appointment_id)


# ---------- rooms ----------
@router.get("/rooms")
def rooms(user: User = Depends(require_feature("appointments"))) -> list:
    return appointment_service.list_rooms()


@router.put("/rooms/{room_id}/status")
def set_room_status(room_id: int, body: RoomStatusUpdate, user: User = Depends(require_feature("appointments"))) -> dict:
    appointment_service.set_room_status(user, room_id, body.status)
    return {"ok": True}


# ---------- patients ----------
@router.get("/patients")
def patients(q: str | None = None, user: User = Depends(require_feature("patients"))) -> list:
    return patient_service.search(user, q)


@router.post("/patients", status_code=201)
def create_patient(body: PatientIn, user: User = Depends(require_feature("patients"))) -> dict:
    return patient_service.create(user, body)


@router.put("/patients/{patient_id}")
def update_patient(patient_id: int, body: PatientIn, user: User = Depends(require_feature("patients"))) -> dict:
    return patient_service.update(user, patient_id, body)


@router.delete("/patients/{patient_id}")
def delete_patient(patient_id: int, user: User = Depends(require_feature("patients"))) -> dict:
    patient_service.delete(user, patient_id)
    return {"ok": True}


@router.get("/patients/{patient_id}/history")
def patient_history(patient_id: int, user: User = Depends(require_feature("patients"))) -> list:
    patient_service.ensure_access(user, patient_id)
    return billing_service.history(user, None, patient_id, None, None)


# ---------- history, invoices, prescriptions ----------
@router.get("/history")
def history(
    q: str | None = None, date_from: date | None = None, date_to: date | None = None,
    user: User = Depends(require_feature("history")),
) -> list:
    return billing_service.history(user, q, None, date_from, date_to)


@router.get("/invoices")
def invoices(status: str | None = None, user: User = Depends(require_feature("invoice"))) -> list:
    return billing_service.invoices(user, status)


@router.get("/invoices/unbilled")
def unbilled(user: User = Depends(require_feature("invoice"))) -> list:
    return billing_service.unbilled(user)


@router.post("/invoices/{invoice_id}/pay")
def pay(invoice_id: int, user: User = Depends(require_feature("invoice"))) -> dict:
    billing_service.pay(user, invoice_id)
    return {"ok": True}


@router.get("/prescriptions")
def prescriptions(q: str | None = None, user: User = Depends(require_feature("prescriptions"))) -> list:
    return billing_service.prescriptions(user, q)