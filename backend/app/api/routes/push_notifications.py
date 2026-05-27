from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.models.web_push_subscription import WebPushSubscription
from app.schemas.push_notification import (
    DeactivatePushTokenResponse,
    SendTestPushRequest,
    SendTestPushResponse,
)
from app.services.web_push_service import (
    WebPushServiceError,
    deactivate_web_push_subscription,
    register_web_push_subscription,
    send_test_web_push_to_current_user,
)


router = APIRouter(prefix="/push", tags=["push"])


class WebPushPublicKeyResponse(BaseModel):
    """Response returned for frontend Web Push setup."""

    enabled: bool
    public_key: str
    subject: str


class WebPushSubscriptionKeysRequest(BaseModel):
    """Browser PushSubscription keys payload."""

    p256dh: str = Field(min_length=10, max_length=2000)
    auth: str = Field(min_length=5, max_length=1000)


class RegisterWebPushSubscriptionRequest(BaseModel):
    """Request payload for registering a standard Web Push subscription."""

    model_config = ConfigDict(populate_by_name=True)

    endpoint: str = Field(min_length=20, max_length=10000)
    expiration_time_ms: int | None = Field(default=None, alias="expirationTime")
    keys: WebPushSubscriptionKeysRequest

    content_encoding: str | None = Field(
        default="aes128gcm",
        alias="contentEncoding",
        max_length=30,
    )
    device_type: str | None = Field(default=None, max_length=60)
    browser_name: str | None = Field(default=None, max_length=120)
    platform: str | None = Field(default=None, max_length=120)


class DeactivateWebPushSubscriptionRequest(BaseModel):
    """Request payload for deactivating a Web Push subscription."""

    endpoint: str = Field(min_length=20, max_length=10000)


class WebPushSubscriptionResponse(BaseModel):
    """Safe Web Push subscription response."""

    id: int
    business_id: int | None
    user_id: int
    device_type: str | None
    browser_name: str | None
    platform: str | None
    is_active: bool
    last_seen_at_utc: str


class RegisterWebPushSubscriptionResponse(BaseModel):
    """Response returned after registering a Web Push subscription."""

    subscription: WebPushSubscriptionResponse
    message: str


def get_user_agent(request: Request) -> str | None:
    """Return normalized user agent from request headers."""

    user_agent = request.headers.get("user-agent")

    if not user_agent:
        return None

    return user_agent.strip()[:1000]


def build_web_push_subscription_response(
    subscription: WebPushSubscription,
) -> WebPushSubscriptionResponse:
    """Build safe Web Push subscription response."""

    return WebPushSubscriptionResponse(
        id=subscription.id,
        business_id=subscription.business_id,
        user_id=subscription.user_id,
        device_type=subscription.device_type,
        browser_name=subscription.browser_name,
        platform=subscription.platform,
        is_active=subscription.is_active,
        last_seen_at_utc=subscription.last_seen_at_utc.isoformat(),
    )


@router.get(
    "/web/public-key",
    response_model=WebPushPublicKeyResponse,
)
def get_web_push_public_key_endpoint() -> WebPushPublicKeyResponse:
    """Return public VAPID key for browser PushManager subscription."""

    return WebPushPublicKeyResponse(
        enabled=settings.web_push_enabled,
        public_key=settings.web_push_vapid_public_key if settings.web_push_enabled else "",
        subject=settings.web_push_vapid_subject if settings.web_push_enabled else "",
    )


@router.post(
    "/web/subscriptions",
    response_model=RegisterWebPushSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_web_push_subscription_endpoint(
    payload: RegisterWebPushSubscriptionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RegisterWebPushSubscriptionResponse:
    """Register current browser/device standard Web Push subscription."""

    try:
        subscription = register_web_push_subscription(
            db=db,
            current_user=current_user,
            endpoint=payload.endpoint,
            p256dh_key=payload.keys.p256dh,
            auth_key=payload.keys.auth,
            expiration_time_ms=payload.expiration_time_ms,
            content_encoding=payload.content_encoding,
            device_type=payload.device_type,
            browser_name=payload.browser_name,
            platform=payload.platform,
            user_agent=get_user_agent(request),
        )

        db.commit()
        db.refresh(subscription)

        return RegisterWebPushSubscriptionResponse(
            subscription=build_web_push_subscription_response(subscription),
            message="Web Push cihazı kaydedildi.",
        )
    except WebPushServiceError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception:
        db.rollback()
        raise


@router.post(
    "/web/subscriptions/deactivate",
    response_model=DeactivatePushTokenResponse,
)
def deactivate_web_push_subscription_endpoint(
    payload: DeactivateWebPushSubscriptionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeactivatePushTokenResponse:
    """Deactivate current browser/device standard Web Push subscription."""

    deactivate_web_push_subscription(
        db=db,
        current_user=current_user,
        endpoint=payload.endpoint,
    )

    db.commit()

    return DeactivatePushTokenResponse(
        is_active=False,
        message="Bu cihaz için Web Push bildirimleri kapatıldı.",
    )


@router.post(
    "/web/test",
    response_model=SendTestPushResponse,
)
def send_test_web_push_endpoint(
    payload: SendTestPushRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SendTestPushResponse:
    """Send test standard Web Push notification to current user's active devices."""

    try:
        result = send_test_web_push_to_current_user(
            db=db,
            current_user=current_user,
            title=payload.title,
            body=payload.body,
        )

        db.commit()

        return SendTestPushResponse(
            attempted_count=result["attempted_count"],
            sent_count=result["sent_count"],
            failed_count=result["failed_count"],
            message="Web Push test bildirimi gönderildi.",
        )
    except WebPushServiceError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception:
        db.rollback()
        raise
