from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.push_notification_log import PushNotificationLog
from app.models.push_notification_token import PushNotificationToken
from app.models.user import User


class FirebasePushSenderError(RuntimeError):
    """Raised when Firebase push sending fails."""


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_firebase_app() -> None:
    """Initialize Firebase Admin app once."""

    try:
        firebase_admin.get_app()
        return
    except ValueError:
        pass

    service_account_file = settings.firebase_service_account_file.strip()

    if not service_account_file:
        raise FirebasePushSenderError(
            "Firebase service account dosya yolu tanımlı değil."
        )

    service_account_path = Path(service_account_file)

    if not service_account_path.exists():
        raise FirebasePushSenderError(
            f"Firebase service account dosyası bulunamadı: {service_account_file}"
        )

    credential = credentials.Certificate(str(service_account_path))
    firebase_admin.initialize_app(credential)


def send_push_message_to_token(
    *,
    fcm_token: str,
    title: str,
    body: str,
    data: dict[str, str] | None = None,
) -> str:
    """Send a single Firebase Cloud Messaging notification."""

    ensure_firebase_app()

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
        token=fcm_token,
    )

    return messaging.send(message)


def send_test_push_to_current_user(
    db: Session,
    *,
    current_user: User,
    title: str,
    body: str,
) -> dict[str, int]:
    """Send test push notification to all active tokens of current user."""

    tokens = (
        db.query(PushNotificationToken)
        .filter(
            PushNotificationToken.user_id == current_user.id,
            PushNotificationToken.is_active.is_(True),
        )
        .order_by(PushNotificationToken.id.desc())
        .all()
    )

    if not tokens:
        raise FirebasePushSenderError("Bu kullanıcı için aktif bildirim cihazı bulunamadı.")

    sent_count = 0
    failed_count = 0
    now = get_utc_now()

    for token in tokens:
        log = PushNotificationLog(
            business_id=current_user.business_id,
            user_id=current_user.id,
            token_id=token.id,
            notification_type="test_push",
            title=title,
            body=body,
            data_json=json.dumps(
                {
                    "type": "test_push",
                    "url": "/",
                },
                ensure_ascii=False,
            ),
            status="pending",
            created_at_utc=now,
            sent_at_utc=None,
        )
        db.add(log)
        db.flush()

        try:
            message_id = send_push_message_to_token(
                fcm_token=token.fcm_token,
                title=title,
                body=body,
                data={
                    "type": "test_push",
                    "url": "/",
                },
            )

            log.status = "sent"
            log.fcm_message_id = message_id
            log.sent_at_utc = get_utc_now()
            sent_count += 1
        except Exception as exc:
            log.status = "failed"
            log.error_message = str(exc)
            failed_count += 1

    db.flush()

    return {
        "attempted_count": len(tokens),
        "sent_count": sent_count,
        "failed_count": failed_count,
    }
