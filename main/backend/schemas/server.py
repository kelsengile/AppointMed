from pydantic import BaseModel, Field, field_validator


class ServerConnectRequest(BaseModel):
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(default=3306, ge=1, le=65535)
    user: str = Field(min_length=1, max_length=64)
    password: str = Field(default="", max_length=255)

    @field_validator("host", "user")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class ServerStatus(BaseModel):
    """Never includes the password."""

    connected: bool
    host: str | None = None
    port: int | None = None
    user: str | None = None
    database: str | None = None