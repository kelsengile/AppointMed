"""Administrator endpoints (users, rooms, settings, reports, audit logs, database tools)."""

from datetime import date

from fastapi import APIRouter, Depends, Query

from backend.core.security import require_feature
from backend.models.domain import User
from backend.routes.database_routes import router as database_router
from backend.schemas.api import (
    ActiveToggle,
    PasswordReset,
    RoomIn,
    ScheduleUpdate,
    SettingsUpdate,
    UserCreate,
    UserUpdate,
)
from backend.services.admin_service import AdminService
from backend.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/admin", tags=["admin"])
router.include_router(database_router)  # /api/admin/database/...
admin_service = AdminService()
dashboard_service = DashboardService()


@router.get("/dashboard")
def dashboard(user: User = Depends(require_feature("admin_dashboard"))) -> dict:
    return dashboard_service.admin()


# ---------- users ----------
@router.get("/users")
def users(role: str | None = None, q: str | None = None, user: User = Depends(require_feature("users"))) -> list:
    return admin_service.list_users(role, q)


@router.get("/doctors")
def doctors(user: User = Depends(require_feature("users"))) -> list:
    return admin_service.doctors()


@router.post("/users", status_code=201)
def create_user(body: UserCreate, user: User = Depends(require_feature("users"))) -> dict:
    return admin_service.create_user(user, body)


@router.put("/users/{user_id}")
def update_user(user_id: int, body: UserUpdate, user: User = Depends(require_feature("users"))) -> dict:
    return admin_service.update_user(user, user_id, body)


@router.post("/users/{user_id}/active")
def set_active(user_id: int, body: ActiveToggle, user: User = Depends(require_feature("users"))) -> dict:
    return admin_service.set_active(user, user_id, body.is_active)


@router.post("/users/{user_id}/password")
def reset_password(user_id: int, body: PasswordReset, user: User = Depends(require_feature("users"))) -> dict:
    admin_service.reset_password(user, user_id, body.new_password)
    return {"ok": True}


@router.get("/users/{user_id}/schedule")
def get_schedule(user_id: int, user: User = Depends(require_feature("users"))) -> list:
    return admin_service.get_schedule(user_id)


@router.put("/users/{user_id}/schedule")
def put_schedule(user_id: int, body: ScheduleUpdate, user: User = Depends(require_feature("users"))) -> list:
    return admin_service.replace_schedule(user, user_id, body.blocks)


# ---------- rooms ----------
@router.get("/rooms")
def rooms(user: User = Depends(require_feature("rooms"))) -> list:
    return admin_service.list_rooms()


@router.post("/rooms", status_code=201)
def create_room(body: RoomIn, user: User = Depends(require_feature("rooms"))) -> list:
    return admin_service.create_room(user, body.room_name, body.status)


@router.put("/rooms/{room_id}")
def update_room(room_id: int, body: RoomIn, user: User = Depends(require_feature("rooms"))) -> list:
    return admin_service.update_room(user, room_id, body.room_name, body.status)


@router.delete("/rooms/{room_id}")
def delete_room(room_id: int, user: User = Depends(require_feature("rooms"))) -> list:
    return admin_service.delete_room(user, room_id)


# ---------- settings, reports, audit ----------
@router.get("/settings")
def get_settings(user: User = Depends(require_feature("settings"))) -> list:
    return admin_service.list_settings()


@router.put("/settings")
def put_settings(body: SettingsUpdate, user: User = Depends(require_feature("settings"))) -> list:
    return admin_service.update_settings(user, body.values)


@router.get("/reports")
def reports(date_from: date | None = None, date_to: date | None = None, user: User = Depends(require_feature("reports"))) -> dict:
    return dashboard_service.report(date_from, date_to)


@router.get("/audit")
def audit(
    q: str | None = None, action: str | None = None,
    limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0),
    user: User = Depends(require_feature("audit")),
) -> dict:
    return admin_service.audit(q, action, limit, offset)