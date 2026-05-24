from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    """Login request payload."""

    business_slug: str | None = Field(
        default=None,
        min_length=3,
        max_length=120,
    )
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=1, max_length=255)

    @field_validator("business_slug", mode="before")
    @classmethod
    def normalize_business_slug(cls, value: object) -> str | None:
        """Normalize optional business slug for scoped business login."""

        if value is None:
            return None

        if not isinstance(value, str):
            return value

        normalized_value = value.strip().lower()

        if not normalized_value:
            return None

        return normalized_value


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
    subscription_access_status: str = "active"
    subscription_status: str | None = None
    subscription_ends_at_utc: datetime | None = None
    subscription_remaining_days: int | None = None
    subscription_is_expired: bool = False
    subscription_lock_reason: str | None = None


class UserSessionResponse(BaseModel):
    """Safe current user session response for frontend routing."""

    id: int
    business_id: int | None
    full_name: str
    username: str
    email: str | None
    role: str
    is_active: bool
    theme_preference: str | None
    dashboard_path: str
    is_super_admin: bool