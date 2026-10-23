"""Login endpoints."""

from fastapi import APIRouter, Depends

from backend.core.deps import get_current_user
from backend.schemas.clinic import LoginRequest
from backend.services.auth_service import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(body: LoginRequest) -> dict:
    return auth_service.login(body.username, body.password)


@router.get("/me")
def me(user: dict = Depends(get_current_user)) -> dict:
    return {"id": user["id"], "username": user["username"], "full_name": user["full_name"], "role": user["role"]}