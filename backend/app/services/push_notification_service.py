from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.push_notification_token import PushNotificationToken
from app.models.user import User


class PushNotificationServiceError(ValueError):
    """Base error for push notification service failures."""


def get_utc_now() -> datetime:
    """Return current UTC datetime."""

    return datetime.now(timezone.utc)


def normalize_optional_text(value: str | None, *, max_length: int) -> str | None:
    """Normalize optional short text fields."""

    if value is None:
        return None

    normalized_value = value.strip()

    if not normalized_value:
        return None

    return normalized_value[:max_length]


def register_push_token(
    db: Session,
    *,
    current_user: User,
    fcm_token: str,
    device_type: str | None,
    browser_name: str | None,
    platform: str | None,
    user_agent: str | None,
) -> PushNotificationToken:
    """Create or update FCM token registration for current user."""

    normalized_token = fcm_token.strip()

    if not normalized_token:
        raise PushNotificationServiceError("Bildirim tokenı boş olamaz.")

    now = get_utc_now()

    token_row = (
        db.query(PushNotificationToken)
        .filter(PushNotificationToken.fcm_token == normalized_token)
        .one_or_none()
    )

    if token_row is None:
        token_row = PushNotificationToken(
            business_id=current_user.business_id,
            user_id=current_user.id,
            fcm_token=normalized_token,
            device_type=normalize_optional_text(device_type, max_length=60),
            browser_name=normalize_optional_text(browser_name, max_length=120),
            platform=normalize_optional_text(platform, max_length=120),
            user_agent=user_agent,
            is_active=True,
            last_seen_at_utc=now,
            created_at_utc=now,
            updated_at_utc=now,
        )
        db.add(token_row)
        db.flush()
        return token_row

    token_row.business_id = current_user.business_id
    token_row.user_id = current_user.id
    token_row.device_type = normalize_optional_text(device_type, max_length=60)
    token_row.browser_name = normalize_optional_text(browser_name, max_length=120)
    token_row.platform = normalize_optional_text(platform, max_length=120)
    token_row.user_agent = user_agent
    token_row.is_active = True
    token_row.last_seen_at_utc = now
    token_row.updated_at_utc = now

    db.flush()
    return token_row


def deactivate_push_token(
    db: Session,
    *,
    current_user: User,
    fcm_token: str,
) -> PushNotificationToken | None:
    """Deactivate a registered push token for current user."""

    normalized_token = fcm_token.strip()

    if not normalized_token:
        return None

    token_row = (
        db.query(PushNotificationToken)
        .filter(
            PushNotificationToken.fcm_token == normalized_token,
            PushNotificationToken.user_id == current_user.id,
        )
        .one_or_none()
    )

    if token_row is None:
        return None

    token_row.is_active = False
    token_row.updated_at_utc = get_utc_now()

    db.flush()
    return token_row
