"""Endpoints used by the public booking page and front page (no login)."""

from datetime import date

from fastapi import APIRouter, Request

from typing import Literal

from fastapi.responses import Response

from backend.core.exceptions import RateLimitError
from backend.core.security import booking_limiter
from backend.schemas.api import BookingRequest
from backend.services.booking_service import BookingService
from backend.services.department_service import DepartmentService
from backend.services.staff_directory_service import StaffDirectoryService
from backend.services.site_service import SiteService

router = APIRouter(prefix="/api/public", tags=["public"])
service = BookingService()
department_service = DepartmentService()
staff_service = StaffDirectoryService()
site_service = SiteService()

@router.get("/catalog")
def catalog() -> dict:
    """Clinic info and bookable doctors."""
    return service.catalog()


@router.get("/departments")
def departments() -> list:
    """Clinical departments for the front page and its 'View all' popup."""
    return department_service.list_public()


@router.get("/staff")
def staff() -> list:
    """All active staff (doctors, nurses, admins) for the front page. Names and roles only."""
    return staff_service.list_public()


@router.get("/staff/{staff_id}")
def staff_member(staff_id: int) -> dict:
    """One staff member's public profile (doctors include their nurses)."""
    return staff_service.get_public(staff_id)


@router.get("/staff/{staff_id}/photo")
def staff_photo(staff_id: int) -> Response:
    """The profile picture the staff member uploaded."""
    data, mime = staff_service.photo(staff_id)
    return Response(content=data, media_type=mime, headers={"Cache-Control": "public, max-age=3600"})


@router.get("/department-icon/{department_id}")
def department_icon(department_id: int) -> Response:
    """An icon an administrator uploaded for a department."""
    data, mime = department_service.icon(department_id)
    return Response(content=data, media_type=mime, headers={"Cache-Control": "public, max-age=3600"})


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

@router.get("/site")
def site() -> dict:
    """Editable front-page texts, links, and whether a custom logo or hero picture exists."""
    return site_service.public()


@router.get("/site-image/{kind}")
def site_image(kind: Literal["logo", "hero"]) -> Response:
    """The custom logo or hero picture."""
    data, mime = site_service.image(kind)
    return Response(content=data, media_type=mime, headers={"Cache-Control": "no-cache"})