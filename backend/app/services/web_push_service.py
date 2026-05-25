from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pywebpush import WebPushException, webpush
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.web_push_subscription import WebPushSubscription


class WebPushServiceError(ValueError):
    """Base error for standard Web Push service failures."""


class WebPushConfigurationError(WebPushServiceError):
    """Raised when Web Push settings are missing or invalid."""


class WebPushSendError(WebPushServiceError):
    """Raised when a Web Push message could not be sent."""


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


def normalize_required_text(
    value: str,
    *,
    field_name: str,
    max_length: int | None = None,
) -> str:
    """Normalize and validate required text fields."""

    normalized_value = value.strip()

    if not normalized_value:
        raise WebPushServiceError(f"{field_name} boş olamaz.")

    if max_length is not None:
        normalized_value = normalized_value[:max_length]

    return normalized_value


def get_endpoint_hash(endpoint: str) -> str:
    """Return stable SHA256 hash for a browser push endpoint."""

    return hashlib.sha256(endpoint.encode("utf-8")).hexdigest()


def get_vapid_private_key_path() -> Path:
    """Return configured VAPID private key path."""

    configured_path = settings.web_push_vapid_private_key_file.strip()

    if not configured_path:
        raise WebPushConfigurationError("Web Push VAPID private key dosyası tanımlı değil.")

    private_key_path = Path(configured_path)

    if not private_key_path.is_absolute():
        private_key_path = Path.cwd() / private_key_path

    if not private_key_path.exists():
        raise WebPushConfigurationError(
            f"Web Push VAPID private key dosyası bulunamadı: {private_key_path}"
        )

    return private_key_path


def ensure_web_push_enabled() -> None:
    """Validate Web Push runtime configuration."""

    if not settings.web_push_enabled:
        raise WebPushConfigurationError("Web Push sistemi aktif değil.")

    if not settings.web_push_vapid_public_key.strip():
        raise WebPushConfigurationError("Web Push VAPID public key tanımlı değil.")

    if not settings.web_push_vapid_subject.strip():
        raise WebPushConfigurationError("Web Push VAPID subject tanımlı değil.")

    get_vapid_private_key_path()


def expiration_time_ms_to_datetime(value: int | None) -> datetime | None:
    """Convert browser PushSubscription expirationTime value from milliseconds."""

    if value is None:
        return None

    if value <= 0:
        return None

    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)


def build_subscription_info(subscription: WebPushSubscription) -> dict[str, Any]:
    """Build pywebpush subscription_info payload from database row."""

    return {
        "endpoint": subscription.endpoint,
        "keys": {
            "p256dh": subscription.p256dh_key,
            "auth": subscription.auth_key,
        },
    }


def build_notification_payload(
    *,
    title: str,
    body: str,
    url: str | None = None,
    icon: str | None = None,
    badge: str | None = None,
    tag: str | None = None,
    data: dict[str, Any] | None = None,
) -> str:
    """Build compact JSON notification payload for service worker."""

    safe_title = normalize_required_text(title, field_name="Bildirim başlığı", max_length=120)
    safe_body = normalize_required_text(body, field_name="Bildirim metni", max_length=250)

    payload_data: dict[str, Any] = {
        "title": safe_title,
        "body": safe_body,
        "url": url or "/",
        "icon": icon or "/icons/icon-192x192.png",
        "badge": badge or "/icons/icon-192x192.png",
        "tag": tag or "missio-notification",
        "data": data or {},
    }

    return json.dumps(payload_data, ensure_ascii=False, separators=(",", ":"))


def register_web_push_subscription(
    db: Session,
    *,
    current_user: User,
    endpoint: str,
    p256dh_key: str,
    auth_key: str,
    expiration_time_ms: int | None,
    content_encoding: str | None,
    device_type: str | None,
    browser_name: str | None,
    platform: str | None,
    user_agent: str | None,
) -> WebPushSubscription:
    """Create or update standard Web Push subscription for current user."""

    ensure_web_push_enabled()

    normalized_endpoint = normalize_required_text(
        endpoint,
        field_name="Web Push endpoint",
    )
    normalized_p256dh_key = normalize_required_text(
        p256dh_key,
        field_name="Web Push p256dh key",
    )
    normalized_auth_key = normalize_required_text(
        auth_key,
        field_name="Web Push auth key",
    )

    normalized_content_encoding = normalize_optional_text(
        content_encoding,
        max_length=30,
    ) or "aes128gcm"

    endpoint_hash = get_endpoint_hash(normalized_endpoint)
    now = get_utc_now()

    subscription = (
        db.query(WebPushSubscription)
        .filter(WebPushSubscription.endpoint_hash == endpoint_hash)
        .one_or_none()
    )

    if subscription is None:
        subscription = WebPushSubscription(
            business_id=current_user.business_id,
            user_id=current_user.id,
            endpoint=normalized_endpoint,
            endpoint_hash=endpoint_hash,
            p256dh_key=normalized_p256dh_key,
            auth_key=normalized_auth_key,
            content_encoding=normalized_content_encoding,
            device_type=normalize_optional_text(device_type, max_length=60),
            browser_name=normalize_optional_text(browser_name, max_length=120),
            platform=normalize_optional_text(platform, max_length=120),
            user_agent=user_agent,
            expiration_time_utc=expiration_time_ms_to_datetime(expiration_time_ms),
            is_active=True,
            last_seen_at_utc=now,
            created_at_utc=now,
            updated_at_utc=now,
        )
        db.add(subscription)
        db.flush()
        return subscription

    subscription.business_id = current_user.business_id
    subscription.user_id = current_user.id
    subscription.endpoint = normalized_endpoint
    subscription.p256dh_key = normalized_p256dh_key
    subscription.auth_key = normalized_auth_key
    subscription.content_encoding = normalized_content_encoding
    subscription.device_type = normalize_optional_text(device_type, max_length=60)
    subscription.browser_name = normalize_optional_text(browser_name, max_length=120)
    subscription.platform = normalize_optional_text(platform, max_length=120)
    subscription.user_agent = user_agent
    subscription.expiration_time_utc = expiration_time_ms_to_datetime(expiration_time_ms)
    subscription.is_active = True
    subscription.last_seen_at_utc = now
    subscription.updated_at_utc = now

    db.flush()
    return subscription


def deactivate_web_push_subscription(
    db: Session,
    *,
    current_user: User,
    endpoint: str,
) -> WebPushSubscription | None:
    """Deactivate a registered Web Push subscription for current user."""

    normalized_endpoint = endpoint.strip()

    if not normalized_endpoint:
        return None

    endpoint_hash = get_endpoint_hash(normalized_endpoint)

    subscription = (
        db.query(WebPushSubscription)
        .filter(
            WebPushSubscription.endpoint_hash == endpoint_hash,
            WebPushSubscription.user_id == current_user.id,
        )
        .one_or_none()
    )

    if subscription is None:
        return None

    subscription.is_active = False
    subscription.updated_at_utc = get_utc_now()

    db.flush()
    return subscription


def send_web_push_to_subscription(
    db: Session,
    *,
    subscription: WebPushSubscription,
    title: str,
    body: str,
    url: str | None = None,
    tag: str | None = None,
    data: dict[str, Any] | None = None,
) -> str:
    """Send one standard Web Push notification."""

    ensure_web_push_enabled()

    if not subscription.is_active:
        raise WebPushSendError("Pasif Web Push aboneliğine bildirim gönderilemez.")

    payload = build_notification_payload(
        title=title,
        body=body,
        url=url,
        tag=tag,
        data=data,
    )

    try:
        response = webpush(
            subscription_info=build_subscription_info(subscription),
            data=payload,
            vapid_private_key=str(get_vapid_private_key_path()),
            vapid_claims={
                "sub": settings.web_push_vapid_subject,
            },
            content_encoding=subscription.content_encoding or "aes128gcm",
        )
    except WebPushException as exc:
        response_status_code = getattr(exc.response, "status_code", None)

        if response_status_code in {404, 410}:
            subscription.is_active = False
            subscription.updated_at_utc = get_utc_now()
            db.flush()

        raise WebPushSendError(f"Web Push gönderilemedi: {exc}") from exc
    except Exception as exc:
        raise WebPushSendError(f"Web Push gönderilemedi: {exc}") from exc

    return str(getattr(response, "status_code", "sent"))


def send_test_web_push_to_current_user(
    db: Session,
    *,
    current_user: User,
    title: str,
    body: str,
) -> dict[str, int]:
    """Send test Web Push notification to current user's active subscriptions."""

    ensure_web_push_enabled()

    subscriptions = (
        db.query(WebPushSubscription)
        .filter(
            WebPushSubscription.user_id == current_user.id,
            WebPushSubscription.is_active.is_(True),
        )
        .order_by(WebPushSubscription.id.desc())
        .all()
    )

    attempted_count = len(subscriptions)
    sent_count = 0
    failed_count = 0

    for subscription in subscriptions:
        try:
            send_web_push_to_subscription(
                db=db,
                subscription=subscription,
                title=title,
                body=body,
                url="/",
                tag="missio-test-web-push",
                data={
                    "type": "test_web_push",
                    "user_id": str(current_user.id),
                },
            )
            sent_count += 1
        except WebPushSendError:
            failed_count += 1

    return {
        "attempted_count": attempted_count,
        "sent_count": sent_count,
        "failed_count": failed_count,
    }
