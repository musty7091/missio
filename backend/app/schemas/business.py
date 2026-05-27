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

    timezone: str = Field(default="Asia/Nicosia", min_length=3, max_length=100)
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
    auto_daily_closing_enabled: bool
    daily_closing_time: str
    created_at: datetime
    updated_at: datetime
    subscription_status: str | None = None
    subscription_billing_period: str | None = None
    subscription_plan_code: str | None = None
    subscription_plan_name: str | None = None
    subscription_ends_at_utc: datetime | None = None
    subscription_max_users: int | None = None
    subscription_remaining_days: int | None = None


class BusinessDailyClosingSettingsResponse(BaseModel):
    """Business-level daily closing settings visible to the business owner."""

    business_id: int
    business_name: str
    timezone: str
    auto_daily_closing_enabled: bool
    daily_closing_time: str


class UpdateBusinessDailyClosingSettingsRequest(BaseModel):
    """Request payload for updating daily closing automation settings."""

    auto_daily_closing_enabled: bool
    daily_closing_time: str = Field(default="23:45", min_length=5, max_length=5)
    timezone: str = Field(default="Asia/Nicosia", min_length=3, max_length=100)

    @field_validator("daily_closing_time", mode="before")
    @classmethod
    def normalize_daily_closing_time(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator("daily_closing_time")
    @classmethod
    def validate_daily_closing_time(cls, value: str) -> str:
        parts = value.split(":")

        if len(parts) != 2:
            raise ValueError("Otomatik kapanış saati HH:MM formatında olmalıdır.")

        try:
            hour = int(parts[0])
            minute = int(parts[1])
        except ValueError as exc:
            raise ValueError("Otomatik kapanış saati HH:MM formatında olmalıdır.") from exc

        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError("Otomatik kapanış saati geçersiz.")

        return f"{hour:02d}:{minute:02d}"

    @field_validator("timezone", mode="before")
    @classmethod
    def normalize_timezone(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()

        return value


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

class SubscriptionPlanResponse(BaseModel):
    """Safe subscription plan response."""

    id: int
    code: str
    name: str
    description: str | None
    max_users: int
    max_managers: int | None
    max_daily_tasks: int | None
    report_retention_days: int
    price_monthly: str | None
    price_yearly: str | None
    currency: str
    display_order: int
    is_active: bool


class ChangeBusinessSubscriptionPlanRequest(BaseModel):
    """Request payload for changing a business subscription plan."""

    plan_code: str = Field(min_length=1, max_length=50)
    duration_days: int = Field(default=30, ge=1, le=3650)
    billing_period: str = Field(default="manual", min_length=3, max_length=30)
    status: str = Field(default="active", min_length=3, max_length=30)
    change_mode: str = Field(default="extend", min_length=3, max_length=30)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("plan_code", "billing_period", "status", "change_mode", mode="before")
    @classmethod
    def normalize_required_text(cls, value: object) -> object:
        """Trim and lowercase required text fields."""

        if isinstance(value, str):
            return value.strip().lower()

        return value

    @field_validator("notes", mode="before")
    @classmethod
    def normalize_optional_notes(cls, value: object) -> object:
        """Trim optional notes and convert empty string to None."""

        if value is None:
            return None

        if not isinstance(value, str):
            return value

        normalized_value = value.strip()

        if not normalized_value:
            return None

        return normalized_value

    @field_validator("billing_period")
    @classmethod
    def validate_billing_period(cls, value: str) -> str:
        """Validate supported billing period."""

        allowed_values = {"manual", "trial", "monthly", "yearly", "custom"}

        if value not in allowed_values:
            raise ValueError("Abonelik ödeme periyodu geçersiz.")

        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        """Validate supported subscription status."""

        allowed_values = {"trialing", "active", "suspended", "cancelled", "expired"}

        if value not in allowed_values:
            raise ValueError("Abonelik durumu geçersiz.")

        return value

    @field_validator("change_mode")
    @classmethod
    def validate_change_mode(cls, value: str) -> str:
        """Validate supported subscription change mode."""

        allowed_values = {"replace", "extend"}

        if value not in allowed_values:
            raise ValueError("Abonelik güncelleme türü geçersiz.")

        return value


class BusinessSubscriptionPlanChangedResponse(BaseModel):
    """Response returned after changing a business subscription plan."""

    subscription: BusinessSubscriptionResponse
    message: str

class BusinessSubscriptionOverviewResponse(BaseModel):
    """Detailed subscription overview for super admin business management."""

    business: BusinessResponse
    current_subscription: BusinessSubscriptionResponse | None
    current_plan: SubscriptionPlanResponse | None
    active_user_count: int
    remaining_days: int | None
    is_expired: bool
    available_plans: list[SubscriptionPlanResponse]


class ExtendBusinessSubscriptionRequest(BaseModel):
    """Request payload for extending current business subscription."""

    duration_days: int = Field(default=30, ge=1, le=3650)
    billing_period: str = Field(default="monthly", min_length=3, max_length=30)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("billing_period", mode="before")
    @classmethod
    def normalize_billing_period(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()

        return value

    @field_validator("billing_period")
    @classmethod
    def validate_billing_period(cls, value: str) -> str:
        allowed_values = {"manual", "trial", "monthly", "yearly", "custom"}

        if value not in allowed_values:
            raise ValueError("Abonelik ödeme periyodu geçersiz.")

        return value

    @field_validator("notes", mode="before")
    @classmethod
    def normalize_optional_notes(cls, value: object) -> object:
        if value is None:
            return None

        if not isinstance(value, str):
            return value

        normalized_value = value.strip()

        if not normalized_value:
            return None

        return normalized_value


class ChangeBusinessPlanRequest(BaseModel):
    """Request payload for upgrading or downgrading a business plan."""

    plan_code: str = Field(min_length=1, max_length=50)
    preserve_remaining_time: bool = True
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("plan_code", mode="before")
    @classmethod
    def normalize_plan_code(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()

        return value

    @field_validator("notes", mode="before")
    @classmethod
    def normalize_optional_notes(cls, value: object) -> object:
        if value is None:
            return None

        if not isinstance(value, str):
            return value

        normalized_value = value.strip()

        if not normalized_value:
            return None

        return normalized_value


class UpdateBusinessSubscriptionStatusRequest(BaseModel):
    """Request payload for suspending or reactivating a business subscription."""

    status: str = Field(min_length=3, max_length=30)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()

        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        allowed_values = {"active", "suspended", "cancelled"}

        if value not in allowed_values:
            raise ValueError("Abonelik durumu geçersiz.")

        return value

    @field_validator("notes", mode="before")
    @classmethod
    def normalize_optional_notes(cls, value: object) -> object:
        if value is None:
            return None

        if not isinstance(value, str):
            return value

        normalized_value = value.strip()

        if not normalized_value:
            return None

        return normalized_value

