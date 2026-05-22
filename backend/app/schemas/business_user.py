from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.roles import UserRole


ALLOWED_CREATE_BUSINESS_USER_ROLES = {
    UserRole.BOSS.value,
    UserRole.MANAGER.value,
    UserRole.STAFF.value,
}

ALLOWED_CHANGE_BUSINESS_USER_ROLES = {
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


class UpdateBusinessUserRequest(BaseModel):
    """Request payload for updating a business scoped user."""

    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    email: str | None = Field(default=None, max_length=255)
    theme_preference: str | None = Field(default=None, max_length=30)
    is_active: bool | None = None

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_optional_full_name(cls, value: object) -> object:
        """Trim optional full_name field."""

        if value is None:
            return None

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

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        """Normalize optional email address for API input."""

        if value is None:
            return None

        return value.strip().lower()

    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> UpdateBusinessUserRequest:
        """Require at least one explicitly provided update field."""

        if not self.model_fields_set:
            raise ValueError("Güncellenecek en az bir alan gönderilmelidir.")

        return self


class ResetBusinessUserPasswordRequest(BaseModel):
    """Request payload for resetting a business scoped user's password."""

    new_password: str = Field(min_length=1, max_length=255)

    @field_validator("new_password", mode="before")
    @classmethod
    def normalize_new_password(cls, value: object) -> object:
        """Trim new password field."""

        if isinstance(value, str):
            return value.strip()

        return value


class ChangeBusinessUserRoleRequest(BaseModel):
    """Request payload for changing a business scoped user's role."""

    role: str = Field(min_length=3, max_length=50)

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, value: object) -> object:
        """Trim and lowercase role field."""

        if isinstance(value, str):
            return value.strip().lower()

        return value

    @field_validator("role")
    @classmethod
    def validate_business_user_role(cls, value: str) -> str:
        """Validate changeable business user role."""

        if value not in ALLOWED_CHANGE_BUSINESS_USER_ROLES:
            raise ValueError(
                "Rol değişikliği sadece manager veya staff için yapılabilir."
            )

        return value


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


class BusinessUserUpdatedResponse(BaseModel):
    """Response returned after updating a business user."""

    user: BusinessUserResponse
    message: str


class BusinessUserPasswordResetResponse(BaseModel):
    """Response returned after resetting a business user's password."""

    user: BusinessUserResponse
    message: str


class BusinessUserRoleChangedResponse(BaseModel):
    """Response returned after changing a business user's role."""

    user: BusinessUserResponse
    message: str