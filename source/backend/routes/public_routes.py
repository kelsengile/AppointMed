"""Endpoints used by the public booking page (no login)."""

from datetime import date

from fastapi import APIRouter, Depends, Query

from backend.core.deps import limit_booking
from backend.schemas.clinic import BookingRequest
from backend.services.booking_service import booking_service

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/doctors")
def doctors() -> dict:
    """Doctors, their specializations and working weekdays, plus whether booking is open."""
    return booking_service.catalog()


@router.get("/doctors/{doctor_id}/slots")
def slots(doctor_id: int, day: date = Query(alias="date")) -> dict:
    """Open times for one doctor on one day."""
    return {"date": day.isoformat(), "slots": booking_service.available_slots(doctor_id, day)}


@router.post("/booking-requests", status_code=201, dependencies=[Depends(limit_booking)])
def create_booking_request(body: BookingRequest) -> dict:
    return booking_service.submit_request(body)