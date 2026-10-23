"""Login, profile, avatar, and password endpoints."""

from fastapi import APIRouter, Depends

from backend.core.security import get_current_user
from backend.models.domain import User
from backend.schemas.api import AvatarUpload, LoginRequest, PasswordChange, ProfileUpdate
from backend.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])
service = AuthService()


@router.post("/login")
def login(body: LoginRequest) -> dict:
    """Sign in and receive a token."""
    return service.login(body.username, body.password)


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    """The signed-in user's profile."""
    return service.profile(user.id)


@router.put("/me")
def update_me(body: ProfileUpdate, user: User = Depends(get_current_user)) -> dict:
    """Change own name and email."""
    return service.update_profile(user.id, body.full_name, body.email)


@router.put("/me/avatar")
def set_avatar(body: AvatarUpload, user: User = Depends(get_current_user)) -> dict:
    """Upload a profile picture (base64 data URL)."""
    return service.set_avatar(user.id, body.image)


@router.delete("/me/avatar")
def remove_avatar(user: User = Depends(get_current_user)) -> dict:
    """Remove the profile picture."""
    return service.remove_avatar(user.id)


@router.post("/change-password")
def change_password(body: PasswordChange, user: User = Depends(get_current_user)) -> dict:
    """Change own password."""
    service.change_password(user.id, body.current_password, body.new_password)
    return {"ok": True}