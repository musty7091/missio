from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


LOCATION_CHECK_STATUS_PENDING = "pending"
LOCATION_CHECK_STATUS_SEEN = "seen"
LOCATION_CHECK_STATUS_SHARED = "shared"
LOCATION_CHECK_STATUS_PERMISSION_DENIED = "permission_denied"
LOCATION_CHECK_STATUS_FAILED = "failed"
LOCATION_CHECK_STATUS_EXPIRED = "expired"
LOCATION_CHECK_STATUS_CANCELLED = "cancelled"

ALLOWED_LOCATION_CHECK_STATUSES = {
    LOCATION_CHECK_STATUS_PENDING,
    LOCATION_CHECK_STATUS_SEEN,
    LOCATION_CHECK_STATUS_SHARED,
    LOCATION_CHECK_STATUS_PERMISSION_DENIED,
    LOCATION_CHECK_STATUS_FAILED,
    LOCATION_CHECK_STATUS_EXPIRED,
    LOCATION_CHECK_STATUS_CANCELLED,
}

LOCATION_CHECK_NOTIFICATION_NOT_ATTEMPTED = "not_attempted"
LOCATION_CHECK_NOTIFICATION_NO_SUBSCRIPTION = "no_subscription"
LOCATION_CHECK_NOTIFICATION_SENT = "sent"
LOCATION_CHECK_NOTIFICATION_PARTIAL_FAILED = "partial_failed"
LOCATION_CHECK_NOTIFICATION_FAILED = "failed"
LOCATION_CHECK_NOTIFICATION_CONFIGURATION_ERROR = "configuration_error"

ALLOWED_LOCATION_CHECK_NOTIFICATION_STATUSES = {
    LOCATION_CHECK_NOTIFICATION_NOT_ATTEMPTED,
    LOCATION_CHECK_NOTIFICATION_NO_SUBSCRIPTION,
    LOCATION_CHECK_NOTIFICATION_SENT,
    LOCATION_CHECK_NOTIFICATION_PARTIAL_FAILED,
    LOCATION_CHECK_NOTIFICATION_FAILED,
    LOCATION_CHECK_NOTIFICATION_CONFIGURATION_ERROR,
}


def normalize_optional_text_value(value: object) -> object:
    """Trim optional text fields and convert empty strings to None."""

    if value is None:
        return None

    if not isinstance(value, str):
        return value

    normalized_value = value.strip()

    if not normalized_value:
        return None

    return normalized_value


def validate_latitude_value(value: float) -> float:
    """Validate latitude range."""

    if value < -90 or value > 90:
        raise ValueError("latitude -90 ile 90 arasında olmalıdır.")

    return value


def validate_longitude_value(value: float) -> float:
    """Validate longitude range."""

    if value < -180 or value > 180:
        raise ValueError("longitude -180 ile 180 arasında olmalıdır.")

    return value


def validate_location_accuracy_value(value: float | None) -> float | None:
    """Validate optional location accuracy value."""

    if value is None:
        return None

    if value < 0:
        raise ValueError("location_accuracy negatif olamaz.")

    return value


class CreateLocationCheckRequest(BaseModel):
    """Request payload for creating manual location check requests."""

    target_user_id: int | None = Field(default=None, gt=0)
    target_user_ids: list[int] | None = Field(default=None, min_length=1, max_length=100)
    request_note: str | None = Field(default=None, max_length=1000)

    @field_validator("request_note", mode="before")
    @classmethod
    def normalize_request_note(cls, value: object) -> object:
        """Normalize optional request note."""

        return normalize_optional_text_value(value)

    @model_validator(mode="after")
    def validate_target_selection(self) -> CreateLocationCheckRequest:
        """Require either one target user or a target user list, not both."""

        has_single_target = self.target_user_id is not None
        has_multiple_targets = self.target_user_ids is not None and len(self.target_user_ids) > 0

        if has_single_target and has_multiple_targets:
            raise ValueError("Aynı anda hem target_user_id hem target_user_ids gönderilemez.")

        if not has_single_target and not has_multiple_targets:
            raise ValueError("Konum yoklaması için en az bir personel seçilmelidir.")

        if self.target_user_ids is not None:
            unique_target_ids = list(dict.fromkeys(self.target_user_ids))

            if len(unique_target_ids) != len(self.target_user_ids):
                raise ValueError("Aynı personel bir konum yoklamasında tekrar seçilemez.")

        return self


class ShareLocationCheckRequest(BaseModel):
    """Request payload for staff location share response."""

    latitude: float
    longitude: float
    location_accuracy: float | None = Field(default=None)

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, value: float) -> float:
        """Validate latitude."""

        return validate_latitude_value(value)

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, value: float) -> float:
        """Validate longitude."""

        return validate_longitude_value(value)

    @field_validator("location_accuracy")
    @classmethod
    def validate_location_accuracy(cls, value: float | None) -> float | None:
        """Validate location accuracy."""

        return validate_location_accuracy_value(value)


class FailLocationCheckRequest(BaseModel):
    """Request payload for staff failure response."""

    response_error_code: str = Field(min_length=2, max_length=80)
    response_error_message: str | None = Field(default=None, max_length=1000)

    @field_validator("response_error_code", mode="before")
    @classmethod
    def normalize_error_code(cls, value: object) -> object:
        """Normalize error code."""

        if isinstance(value, str):
            return value.strip().lower()

        return value

    @field_validator("response_error_message", mode="before")
    @classmethod
    def normalize_error_message(cls, value: object) -> object:
        """Normalize optional error message."""

        return normalize_optional_text_value(value)


class LocationCheckResponse(BaseModel):
    """Safe manual location check response."""

    id: int
    business_id: int
    request_group_id: str | None
    requested_by_user_id: int | None
    requested_by_user_full_name: str | None
    target_user_id: int
    target_user_full_name: str | None
    target_username: str | None
    status: str
    request_note: str | None
    notification_status: str
    notification_attempted_count: int
    notification_sent_count: int
    notification_failed_count: int
    last_notification_attempt_at_utc: datetime | None
    staff_seen_at_utc: datetime | None
    responded_at_utc: datetime | None
    expires_at_utc: datetime | None
    latitude: float | None
    longitude: float | None
    location_accuracy: float | None
    response_error_code: str | None
    response_error_message: str | None
    requested_at_utc: datetime
    created_at_utc: datetime
    updated_at_utc: datetime


class LocationCheckCreatedResponse(BaseModel):
    """Response returned after creating location check requests."""

    checks: list[LocationCheckResponse]
    created_count: int
    message: str


class LocationCheckListResponse(BaseModel):
    """Paginated manual location check list response."""

    checks: list[LocationCheckResponse]
    total_count: int


class LocationCheckUpdatedResponse(BaseModel):
    """Response returned after updating one location check."""

    check: LocationCheckResponse
    message: str
