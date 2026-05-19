from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request payload."""

    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    """Successful authentication response."""

    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class TokenPayloadResponse(BaseModel):
    """Debug-safe token payload response."""

    subject: str
    role: str
    business_id: int | None
    issued_at: str
    expires_at: str


class UserMeResponse(BaseModel):
    """Safe current user response."""

    id: int
    business_id: int | None
    full_name: str
    username: str
    email: str | None
    role: str
    is_active: bool
    theme_preference: str | None
