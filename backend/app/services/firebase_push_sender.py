from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user import User


class FirebasePushSenderError(RuntimeError):
    """Raised when legacy Firebase push code is called after Firebase removal."""


def send_test_push_to_current_user(
    db: Session,
    *,
    current_user: User,
    title: str,
    body: str,
) -> dict[str, int]:
    """Legacy FCM entry point kept as a safe stub for old imports.

    Missio no longer uses Firebase Cloud Messaging. Standard Web Push/VAPID is
    the active notification path. New code must call web_push_service instead.
    """

    raise FirebasePushSenderError(
        "Firebase Cloud Messaging devre dışı. Standart Web Push kullanılmalıdır."
    )
