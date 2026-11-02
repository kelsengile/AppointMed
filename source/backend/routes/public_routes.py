"""Endpoints used by the public booking page (no login)."""

from datetime import date

from fastapi import APIRouter, Request

from backend.core.exceptions import RateLimitError
from backend.core.security import booking_limiter
from backend.schemas.api import BookingRequest
from backend.services.booking_service import BookingService

router = APIRouter(prefix="/api/public", tags=["public"])
service = BookingService()


@router.get("/catalog")
def catalog() -> dict:
    """Clinic info and bookable doctors."""
    return service.catalog()


@router.get("/slots")
def slots(doctor_id: int, day: date) -> dict:
    """Open times for a doctor on a day."""
    return service.slots(doctor_id, day)


@router.get("/calendar")
def calendar(doctor_id: int, date_from: date, date_to: date) -> dict:
    """Working weekdays and fully booked days for the booking calendar."""
    return service.calendar(doctor_id, date_from, date_to)


@router.post("/bookings", status_code=201)
def book(body: BookingRequest, request: Request) -> dict:
    """Submit an appointment request. Limited per visitor to discourage spam."""
    key = request.client.host if request.client else "unknown"
    if booking_limiter.is_blocked(key):
        raise RateLimitError("You have sent several requests already. Please wait a few minutes.")
    receipt = service.book(body)
    booking_limiter.record(key)
    return receipt