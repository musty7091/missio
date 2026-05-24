from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.push_notification_token import PushNotificationToken
from app.models.user import User
from app.schemas.push_notification import (
    DeactivatePushTokenRequest,
    DeactivatePushTokenResponse,
    PushTokenResponse,
    RegisterPushTokenRequest,
    RegisterPushTokenResponse,
    SendTestPushRequest,
    SendTestPushResponse,
)
from app.services.firebase_push_sender import (
    FirebasePushSenderError,
    send_test_push_to_current_user,
)
from app.services.push_notification_service import (
    PushNotificationServiceError,
    deactivate_push_token,
    register_push_token,
)


router = APIRouter(prefix="/push", tags=["push"])


def get_user_agent(request: Request) -> str | None:
    """Return normalized user agent from request headers."""

    user_agent = request.headers.get("user-agent")

    if not user_agent:
        return None

    return user_agent.strip()[:1000]


def build_push_token_response(token: PushNotificationToken) -> PushTokenResponse:
    """Build safe push token response."""

    return PushTokenResponse(
        id=token.id,
        business_id=token.business_id,
        user_id=token.user_id,
        device_type=token.device_type,
        browser_name=token.browser_name,
        platform=token.platform,
        is_active=token.is_active,
        last_seen_at_utc=token.last_seen_at_utc.isoformat(),
    )


@router.post(
    "/tokens",
    response_model=RegisterPushTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_push_token_endpoint(
    payload: RegisterPushTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RegisterPushTokenResponse:
    """Register current browser/device FCM token."""

    try:
        token = register_push_token(
            db=db,
            current_user=current_user,
            fcm_token=payload.fcm_token,
            device_type=payload.device_type,
            browser_name=payload.browser_name,
            platform=payload.platform,
            user_agent=get_user_agent(request),
        )

        db.commit()
        db.refresh(token)

        return RegisterPushTokenResponse(
            token=build_push_token_response(token),
            message="Bildirim cihazı kaydedildi.",
        )
    except PushNotificationServiceError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception:
        db.rollback()
        raise



@router.post(
    "/tokens/deactivate",
    response_model=DeactivatePushTokenResponse,
)
def deactivate_push_token_endpoint(
    payload: DeactivatePushTokenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeactivatePushTokenResponse:
    """Deactivate current browser/device FCM token."""

    deactivate_push_token(
        db=db,
        current_user=current_user,
        fcm_token=payload.fcm_token,
    )

    db.commit()

    return DeactivatePushTokenResponse(
        is_active=False,
        message="Bu cihaz için bildirimler kapatıldı.",
    )



@router.post(
    "/test",
    response_model=SendTestPushResponse,
)
def send_test_push_endpoint(
    payload: SendTestPushRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SendTestPushResponse:
    """Send test push notification to current user's active devices."""

    try:
        result = send_test_push_to_current_user(
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
            message="Test bildirimi gönderildi.",
        )
    except FirebasePushSenderError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception:
        db.rollback()
        raise
