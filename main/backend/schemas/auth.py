from pydantic import BaseModel, Field

from backend.models.user import Role, User


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: Role
    specialization: str | None = None

    @classmethod
    def from_model(cls, user: User) -> "UserOut":
        return cls(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            specialization=user.specialization,
        )


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut