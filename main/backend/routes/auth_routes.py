from fastapi import APIRouter, Depends

from backend.core.permissions import get_current_user
from backend.models.user import User
from backend.schemas.auth import LoginRequest, LoginResponse, UserOut
from backend.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest) -> LoginResponse:
    return AuthService().login(request.username, request.password)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.from_model(user)