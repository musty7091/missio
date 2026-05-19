from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.core.roles import UserRole


ALLOWED_CREATE_BUSINESS_USER_ROLES = {
    UserRole.BOSS.value,
    UserRole.BUSINESS_OWNER.value,
    UserRole.MANAGER.value,
    UserRole.STAFF.value,
}


class CreateBusinessUserRequest(BaseModel):
    """Request payload for creating a business scoped user."""

    full_name: str = Field(min_length=2, max_length=200)
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=1, max_length=255)
    role: str = Field(min_length=3, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    theme_preference: str | None = Field(default=None, max_length=30)

    @field_validator("full_name", "username", "role", mode="before")
    @classmethod
    def normalize_required_text(cls, value: object) -> object:
        """Trim required text fields."""

        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator("email", "theme_preference", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: object) -> object:
        """Trim optional text fields and convert empty strings to None."""

        if value is None:
            return None

        if not isinstance(value, str):
            return value

        normalized_value = value.strip()

        if not normalized_value:
            return None

        return normalized_value

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        """Normalize username for API input."""

        return value.strip().lower()

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        """Normalize optional email address for API input."""

        if value is None:
            return None

        return value.strip().lower()

    @field_validator("role")
    @classmethod
    def validate_business_user_role(cls, value: str) -> str:
        """Validate business user role."""

        normalized_role = value.strip().lower()

        if normalized_role not in ALLOWED_CREATE_BUSINESS_USER_ROLES:
            raise ValueError("İşletme kullanıcısı rolü geçersiz.")

        return normalized_role


class BusinessUserResponse(BaseModel):
    """Safe business user response."""

    id: int
    business_id: int
    full_name: str
    username: str
    email: str | None
    role: str
    is_active: bool
    theme_preference: str | None


class BusinessUserCreatedResponse(BaseModel):
    """Response returned after creating a business user."""

    user: BusinessUserResponse
    message: str