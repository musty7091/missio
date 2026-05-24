from __future__ import annotations

from pydantic import BaseModel, Field


class RegisterPushTokenRequest(BaseModel):
    """Request payload for registering a browser/device push token."""

    fcm_token: str = Field(min_length=20, max_length=5000)
    device_type: str | None = Field(default=None, max_length=60)
    browser_name: str | None = Field(default=None, max_length=120)
    platform: str | None = Field(default=None, max_length=120)


class PushTokenResponse(BaseModel):
    """Safe push token response."""

    id: int
    business_id: int | None
    user_id: int
    device_type: str | None
    browser_name: str | None
    platform: str | None
    is_active: bool
    last_seen_at_utc: str


class RegisterPushTokenResponse(BaseModel):
    """Response returned after registering a push token."""

    token: PushTokenResponse
    message: str



class DeactivatePushTokenRequest(BaseModel):
    """Request payload for deactivating a browser/device push token."""

    fcm_token: str = Field(min_length=20, max_length=5000)


class DeactivatePushTokenResponse(BaseModel):
    """Response returned after deactivating a push token."""

    is_active: bool
    message: str



class SendTestPushRequest(BaseModel):
    """Request payload for sending a test push notification."""

    title: str = Field(default="Missio test bildirimi", min_length=1, max_length=120)
    body: str = Field(default="Bu cihaz Missio push bildirimlerini alabiliyor.", min_length=1, max_length=250)


class SendTestPushResponse(BaseModel):
    """Response returned after sending a test push notification."""

    attempted_count: int
    sent_count: int
    failed_count: int
    message: str
