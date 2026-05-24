from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.roles import UserRole


class CreateBusinessWithOwnerRequest(BaseModel):
    """Request payload for creating a business with its first owner user."""

    business_name: str = Field(min_length=2, max_length=200)
    business_slug: str = Field(min_length=3, max_length=120)

    owner_full_name: str = Field(min_length=2, max_length=200)
    owner_username: str = Field(min_length=3, max_length=100)
    owner_password: str = Field(min_length=1, max_length=255)

    business_owner_name: str | None = Field(default=None, max_length=200)
    business_phone: str | None = Field(default=None, max_length=50)
    business_email: str | None = Field(default=None, max_length=255)
    business_address: str | None = Field(default=None, max_length=500)

    owner_email: str | None = Field(default=None, max_length=255)
    owner_role: str = Field(default=UserRole.BOSS.value, min_length=3, max_length=50)

    timezone: str = Field(default="Europe/Istanbul", min_length=3, max_length=100)
    default_theme: str = Field(default="dark", min_length=2, max_length=30)

    @field_validator(
        "business_name",
        "business_slug",
        "owner_full_name",
        "owner_username",
        "owner_role",
        "timezone",
        "default_theme",
        mode="before",
    )
    @classmethod
    def normalize_required_text(cls, value: object) -> object:
        """Trim required text fields."""

        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator(
        "business_owner_name",
        "business_phone",
        "business_email",
        "business_address",
        "owner_email",
        mode="before",
    )
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

    @field_validator("business_slug")
    @classmethod
    def normalize_business_slug(cls, value: str) -> str:
        """Normalize business slug input before service-level slug validation."""

        return value.strip().lower()

    @field_validator("owner_username")
    @classmethod
    def normalize_owner_username(cls, value: str) -> str:
        """Normalize owner username."""

        return value.strip().lower()

    @field_validator("business_email", "owner_email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        """Normalize optional email fields."""

        if value is None:
            return None

        return value.strip().lower()

    @field_validator("owner_role")
    @classmethod
    def validate_owner_role(cls, value: str) -> str:
        """Only boss can be created as first business owner."""

        normalized_role = value.strip().lower()

        if normalized_role != UserRole.BOSS.value:
            raise ValueError("İlk işletme sahibi rolü boss olmalıdır.")

        return normalized_role


class BusinessResponse(BaseModel):
    """Safe business response."""

    id: int
    name: str
    slug: str
    logo_path: str | None
    owner_name: str | None
    phone: str | None
    email: str | None
    address: str | None
    timezone: str
    default_theme: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class BusinessOwnerUserResponse(BaseModel):
    """Safe first owner user response."""

    id: int
    business_id: int
    full_name: str
    username: str
    email: str | None
    role: str
    is_active: bool


class BusinessSubscriptionResponse(BaseModel):
    """Safe business subscription response."""

    id: int
    business_id: int
    plan_id: int
    status: str
    billing_period: str
    starts_at_utc: datetime
    ends_at_utc: datetime | None
    is_current: bool
    max_users_snapshot: int
    max_managers_snapshot: int | None
    max_daily_tasks_snapshot: int | None
    report_retention_days_snapshot: int


class BusinessWithOwnerCreatedResponse(BaseModel):
    """Response returned after creating a business with owner and subscription."""

    business: BusinessResponse
    owner_user: BusinessOwnerUserResponse
    subscription: BusinessSubscriptionResponse | None
    message: str
