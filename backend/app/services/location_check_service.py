from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.roles import UserRole
from app.models.location_check import LocationCheck
from app.models.user import User
from app.models.web_push_subscription import WebPushSubscription
from app.schemas.location_check import (
    LOCATION_CHECK_NOTIFICATION_CONFIGURATION_ERROR,
    LOCATION_CHECK_NOTIFICATION_FAILED,
    LOCATION_CHECK_NOTIFICATION_NO_SUBSCRIPTION,
    LOCATION_CHECK_NOTIFICATION_NOT_ATTEMPTED,
    LOCATION_CHECK_NOTIFICATION_PARTIAL_FAILED,
    LOCATION_CHECK_NOTIFICATION_SENT,
    LOCATION_CHECK_STATUS_FAILED,
    LOCATION_CHECK_STATUS_PENDING,
    LOCATION_CHECK_STATUS_PERMISSION_DENIED,
    LOCATION_CHECK_STATUS_SEEN,
    LOCATION_CHECK_STATUS_SHARED,
    LocationCheckResponse,
)
from app.services.access_control_service import ensure_business_scope
from app.services.web_push_service import (
    WebPushConfigurationError,
    WebPushServiceError,
    send_web_push_to_subscription,
)


class LocationCheckServiceError(ValueError):
    """Base error for manual location check service failures."""


class LocationCheckPermissionError(LocationCheckServiceError):
    """Raised when user has no permission for location check operation."""


class LocationCheckNotFoundError(LocationCheckServiceError):
    """Raised when location check is not found."""


class InvalidLocationCheckTargetError(LocationCheckServiceError):
    """Raised when selected target user cannot receive a location check request."""


class InvalidLocationCheckStateError(LocationCheckServiceError):
    """Raised when location check state does not allow requested operation."""


@dataclass(frozen=True)
class LocationCheckListResult:
    """Location check list result."""

    checks: list[LocationCheck]
    total_count: int


LOCATION_CHECK_MANAGER_ROLES = {
    UserRole.SUPER_ADMIN.value,
    UserRole.BOSS.value,
    UserRole.MANAGER.value,
}

LOCATION_CHECK_TARGET_ROLES = {
    UserRole.MANAGER.value,
    UserRole.STAFF.value,
}

logger = logging.getLogger(__name__)


def get_utc_now() -> datetime:
    """Return current UTC datetime."""

    return datetime.now(timezone.utc)


def normalize_optional_text(value: str | None, *, max_length: int) -> str | None:
    """Normalize optional text value."""

    if value is None:
        return None

    normalized_value = value.strip()

    if not normalized_value:
        return None

    return normalized_value[:max_length]


def ensure_location_check_manager_access(
    current_user: User,
    *,
    business_id: int,
) -> None:
    """Ensure current user can manage manual location checks."""

    ensure_business_scope(current_user, business_id)

    if current_user.role in LOCATION_CHECK_MANAGER_ROLES:
        return

    raise LocationCheckPermissionError("Bu işlem için konum yoklama yetkiniz yok.")


def ensure_location_check_target_is_valid(
    target_user: User,
    *,
    business_id: int,
) -> None:
    """Ensure target user can receive a manual location check request."""

    if target_user.business_id != business_id:
        raise InvalidLocationCheckTargetError(
            "Konum istenecek kullanıcı bu işletmeye ait değil."
        )

    if not target_user.is_active:
        raise InvalidLocationCheckTargetError("Pasif kullanıcıdan konum istenemez.")

    if target_user.role not in LOCATION_CHECK_TARGET_ROLES:
        raise InvalidLocationCheckTargetError(
            "Konum sadece manager veya personel kullanıcısından istenebilir."
        )


def ensure_can_request_location_check_for_user(
    current_user: User,
    *,
    target_user: User,
    business_id: int,
) -> None:
    """Ensure current user can request a location check from target user."""

    ensure_location_check_manager_access(current_user, business_id=business_id)
    ensure_location_check_target_is_valid(target_user, business_id=business_id)

    if current_user.role == UserRole.SUPER_ADMIN.value:
        return

    if current_user.role == UserRole.BOSS.value:
        return

    if current_user.role == UserRole.MANAGER.value:
        if target_user.role == UserRole.STAFF.value:
            return

        raise LocationCheckPermissionError(
            "Manager sadece personel kullanıcısından konum isteyebilir."
        )

    raise LocationCheckPermissionError("Bu kullanıcı konum yoklaması isteyemez.")


def ensure_staff_can_access_location_check(
    current_user: User,
    *,
    location_check: LocationCheck,
) -> None:
    """Ensure staff user can access own location check request."""

    ensure_business_scope(current_user, location_check.business_id)

    if location_check.target_user_id == current_user.id:
        return

    raise LocationCheckPermissionError("Bu konum yoklamasına erişim yetkiniz yok.")


def get_location_check_or_error(db: Session, *, location_check_id: int) -> LocationCheck:
    """Return location check by id or raise."""

    location_check = db.get(LocationCheck, location_check_id)

    if location_check is None:
        raise LocationCheckNotFoundError("Konum yoklama isteği bulunamadı.")

    return location_check


def get_user_display_map(db: Session, *, user_ids: set[int]) -> dict[int, User]:
    """Return user map for safe response building."""

    safe_user_ids = {user_id for user_id in user_ids if user_id > 0}

    if not safe_user_ids:
        return {}

    users = db.query(User).filter(User.id.in_(sorted(safe_user_ids))).all()

    return {user.id: user for user in users}


def build_location_check_response(
    location_check: LocationCheck,
    *,
    db: Session,
) -> LocationCheckResponse:
    """Build safe location check response."""

    user_ids: set[int] = {location_check.target_user_id}

    if location_check.requested_by_user_id is not None:
        user_ids.add(location_check.requested_by_user_id)

    user_map = get_user_display_map(db, user_ids=user_ids)
    requested_by_user = (
        user_map.get(location_check.requested_by_user_id)
        if location_check.requested_by_user_id is not None
        else None
    )
    target_user = user_map.get(location_check.target_user_id)

    return LocationCheckResponse(
        id=location_check.id,
        business_id=location_check.business_id,
        request_group_id=location_check.request_group_id,
        requested_by_user_id=location_check.requested_by_user_id,
        requested_by_user_full_name=(
            requested_by_user.full_name if requested_by_user is not None else None
        ),
        target_user_id=location_check.target_user_id,
        target_user_full_name=target_user.full_name if target_user is not None else None,
        target_username=target_user.username if target_user is not None else None,
        status=location_check.status,
        request_note=location_check.request_note,
        notification_status=location_check.notification_status,
        notification_attempted_count=location_check.notification_attempted_count,
        notification_sent_count=location_check.notification_sent_count,
        notification_failed_count=location_check.notification_failed_count,
        last_notification_attempt_at_utc=location_check.last_notification_attempt_at_utc,
        staff_seen_at_utc=location_check.staff_seen_at_utc,
        responded_at_utc=location_check.responded_at_utc,
        expires_at_utc=location_check.expires_at_utc,
        latitude=location_check.latitude,
        longitude=location_check.longitude,
        location_accuracy=location_check.location_accuracy,
        response_error_code=location_check.response_error_code,
        response_error_message=location_check.response_error_message,
        requested_at_utc=location_check.requested_at_utc,
        created_at_utc=location_check.created_at_utc,
        updated_at_utc=location_check.updated_at_utc,
    )


def build_location_check_responses(
    checks: list[LocationCheck],
    *,
    db: Session,
) -> list[LocationCheckResponse]:
    """Build safe location check response list."""

    user_ids: set[int] = set()

    for location_check in checks:
        user_ids.add(location_check.target_user_id)

        if location_check.requested_by_user_id is not None:
            user_ids.add(location_check.requested_by_user_id)

    user_map = get_user_display_map(db, user_ids=user_ids)
    responses: list[LocationCheckResponse] = []

    for location_check in checks:
        requested_by_user = (
            user_map.get(location_check.requested_by_user_id)
            if location_check.requested_by_user_id is not None
            else None
        )
        target_user = user_map.get(location_check.target_user_id)

        responses.append(
            LocationCheckResponse(
                id=location_check.id,
                business_id=location_check.business_id,
                request_group_id=location_check.request_group_id,
                requested_by_user_id=location_check.requested_by_user_id,
                requested_by_user_full_name=(
                    requested_by_user.full_name if requested_by_user is not None else None
                ),
                target_user_id=location_check.target_user_id,
                target_user_full_name=(
                    target_user.full_name if target_user is not None else None
                ),
                target_username=target_user.username if target_user is not None else None,
                status=location_check.status,
                request_note=location_check.request_note,
                notification_status=location_check.notification_status,
                notification_attempted_count=location_check.notification_attempted_count,
                notification_sent_count=location_check.notification_sent_count,
                notification_failed_count=location_check.notification_failed_count,
                last_notification_attempt_at_utc=(
                    location_check.last_notification_attempt_at_utc
                ),
                staff_seen_at_utc=location_check.staff_seen_at_utc,
                responded_at_utc=location_check.responded_at_utc,
                expires_at_utc=location_check.expires_at_utc,
                latitude=location_check.latitude,
                longitude=location_check.longitude,
                location_accuracy=location_check.location_accuracy,
                response_error_code=location_check.response_error_code,
                response_error_message=location_check.response_error_message,
                requested_at_utc=location_check.requested_at_utc,
                created_at_utc=location_check.created_at_utc,
                updated_at_utc=location_check.updated_at_utc,
            )
        )

    return responses


def create_location_checks(
    db: Session,
    *,
    current_user: User,
    business_id: int,
    target_user_ids: list[int],
    request_note: str | None = None,
) -> list[LocationCheck]:
    """Create manual location check requests."""

    ensure_location_check_manager_access(current_user, business_id=business_id)

    unique_target_user_ids = sorted({user_id for user_id in target_user_ids if user_id > 0})

    if not unique_target_user_ids:
        raise InvalidLocationCheckTargetError(
            "Konum yoklaması için en az bir personel seçilmelidir."
        )

    if len(unique_target_user_ids) > 100:
        raise InvalidLocationCheckTargetError(
            "Tek seferde en fazla 100 kişiden konum istenebilir."
        )

    target_users = (
        db.query(User)
        .filter(User.id.in_(unique_target_user_ids))
        .order_by(User.id.asc())
        .all()
    )

    target_user_map = {user.id: user for user in target_users}
    missing_user_ids = [
        user_id for user_id in unique_target_user_ids if user_id not in target_user_map
    ]

    if missing_user_ids:
        raise InvalidLocationCheckTargetError(
            "Konum istenecek kullanıcılardan biri bulunamadı."
        )

    for target_user in target_users:
        ensure_can_request_location_check_for_user(
            current_user,
            target_user=target_user,
            business_id=business_id,
        )

    now = get_utc_now()
    request_group_id = uuid4().hex
    checks: list[LocationCheck] = []

    for target_user in target_users:
        location_check = LocationCheck(
            business_id=business_id,
            request_group_id=request_group_id,
            requested_by_user_id=current_user.id,
            target_user_id=target_user.id,
            status=LOCATION_CHECK_STATUS_PENDING,
            request_note=normalize_optional_text(request_note, max_length=1000),
            notification_status=LOCATION_CHECK_NOTIFICATION_NOT_ATTEMPTED,
            notification_attempted_count=0,
            notification_sent_count=0,
            notification_failed_count=0,
            last_notification_attempt_at_utc=None,
            staff_seen_at_utc=None,
            responded_at_utc=None,
            expires_at_utc=None,
            latitude=None,
            longitude=None,
            location_accuracy=None,
            response_error_code=None,
            response_error_message=None,
            ip_address=None,
            user_agent=None,
            requested_at_utc=now,
            created_at_utc=now,
            updated_at_utc=now,
        )
        db.add(location_check)
        checks.append(location_check)

    db.flush()
    return checks


def build_location_check_web_push_url(location_check: LocationCheck) -> str:
    """Return frontend deep-link URL for location check notification."""

    return f"/?missioOpen=location-check&missioLocationCheckId={location_check.id}"


def get_active_web_push_subscriptions_for_user(
    db: Session,
    *,
    business_id: int,
    user_id: int,
) -> list[WebPushSubscription]:
    """Return active Web Push subscriptions for one user."""

    return (
        db.query(WebPushSubscription)
        .filter(
            WebPushSubscription.business_id == business_id,
            WebPushSubscription.user_id == user_id,
            WebPushSubscription.is_active.is_(True),
        )
        .order_by(WebPushSubscription.id.desc())
        .all()
    )


def send_location_check_web_push_safely(
    db: Session,
    *,
    location_check: LocationCheck,
) -> None:
    """Best-effort location check Web Push delivery."""

    now = get_utc_now()
    subscriptions = get_active_web_push_subscriptions_for_user(
        db=db,
        business_id=location_check.business_id,
        user_id=location_check.target_user_id,
    )

    location_check.notification_attempted_count = len(subscriptions)
    location_check.notification_sent_count = 0
    location_check.notification_failed_count = 0
    location_check.last_notification_attempt_at_utc = now
    location_check.updated_at_utc = now

    if not subscriptions:
        location_check.notification_status = LOCATION_CHECK_NOTIFICATION_NO_SUBSCRIPTION
        db.flush()
        logger.warning(
            "MISSIO_LOCATION_CHECK_PUSH_NO_SUBSCRIPTION location_check_id=%s target_user_id=%s business_id=%s",
            location_check.id,
            location_check.target_user_id,
            location_check.business_id,
        )
        return

    for subscription in subscriptions:
        try:
            send_web_push_to_subscription(
                db=db,
                subscription=subscription,
                title="Konum yoklaması istendi",
                body="Patron/manager konumunu paylaşmanı istiyor.",
                url=build_location_check_web_push_url(location_check),
                tag=f"missio-location-check-{location_check.id}",
                data={
                    "type": "location_check_requested",
                    "location_check_id": str(location_check.id),
                    "locationCheckId": str(location_check.id),
                    "business_id": str(location_check.business_id),
                    "businessId": str(location_check.business_id),
                    "url": build_location_check_web_push_url(location_check),
                },
            )
            location_check.notification_sent_count += 1
        except WebPushConfigurationError as exc:
            location_check.notification_failed_count += 1
            logger.warning(
                "MISSIO_LOCATION_CHECK_PUSH_CONFIGURATION_ERROR location_check_id=%s subscription_id=%s user_id=%s error=%s",
                location_check.id,
                subscription.id,
                subscription.user_id,
                exc,
            )
        except WebPushServiceError as exc:
            location_check.notification_failed_count += 1
            logger.warning(
                "MISSIO_LOCATION_CHECK_PUSH_FAILED location_check_id=%s subscription_id=%s user_id=%s error=%s",
                location_check.id,
                subscription.id,
                subscription.user_id,
                exc,
            )
        except Exception as exc:
            location_check.notification_failed_count += 1
            logger.warning(
                "MISSIO_LOCATION_CHECK_PUSH_UNEXPECTED_ERROR location_check_id=%s subscription_id=%s user_id=%s error=%s",
                location_check.id,
                subscription.id,
                subscription.user_id,
                exc,
            )

    if location_check.notification_sent_count > 0 and location_check.notification_failed_count == 0:
        location_check.notification_status = LOCATION_CHECK_NOTIFICATION_SENT
    elif location_check.notification_sent_count > 0:
        location_check.notification_status = LOCATION_CHECK_NOTIFICATION_PARTIAL_FAILED
    elif subscriptions:
        location_check.notification_status = LOCATION_CHECK_NOTIFICATION_FAILED
    else:
        location_check.notification_status = LOCATION_CHECK_NOTIFICATION_NO_SUBSCRIPTION

    db.flush()


def send_location_check_notifications_safely(
    db: Session,
    *,
    checks: list[LocationCheck],
) -> None:
    """Send best-effort notifications for location check list."""

    for location_check in checks:
        try:
            send_location_check_web_push_safely(
                db=db,
                location_check=location_check,
            )
        except WebPushConfigurationError:
            location_check.notification_status = LOCATION_CHECK_NOTIFICATION_CONFIGURATION_ERROR
            location_check.notification_failed_count = location_check.notification_attempted_count
            location_check.updated_at_utc = get_utc_now()
            db.flush()
        except Exception as exc:
            location_check.notification_status = LOCATION_CHECK_NOTIFICATION_FAILED
            location_check.updated_at_utc = get_utc_now()
            db.flush()
            logger.warning(
                "MISSIO_LOCATION_CHECK_NOTIFICATION_SIDE_EFFECT_FAILED location_check_id=%s error=%s",
                location_check.id,
                exc,
            )


def list_location_checks_for_business(
    db: Session,
    *,
    current_user: User,
    business_id: int,
    status: str | None = None,
    target_user_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> LocationCheckListResult:
    """List location checks for boss/manager screen."""

    ensure_location_check_manager_access(current_user, business_id=business_id)

    safe_limit = max(1, min(limit, 100))
    safe_offset = max(0, offset)

    query = select(LocationCheck).where(LocationCheck.business_id == business_id)
    count_query = select(func.count(LocationCheck.id)).where(
        LocationCheck.business_id == business_id
    )

    if status is not None:
        query = query.where(LocationCheck.status == status)
        count_query = count_query.where(LocationCheck.status == status)

    if target_user_id is not None:
        query = query.where(LocationCheck.target_user_id == target_user_id)
        count_query = count_query.where(LocationCheck.target_user_id == target_user_id)

    checks = list(
        db.execute(
            query.order_by(LocationCheck.created_at_utc.desc())
            .offset(safe_offset)
            .limit(safe_limit)
        )
        .scalars()
        .all()
    )
    total_count = int(db.execute(count_query).scalar_one())

    return LocationCheckListResult(checks=checks, total_count=total_count)


def list_pending_location_checks_for_staff(
    db: Session,
    *,
    current_user: User,
) -> LocationCheckListResult:
    """List pending/seen location checks for current staff user."""

    if current_user.business_id is None:
        raise LocationCheckPermissionError("Kullanıcının işletme kapsamı yok.")

    query = select(LocationCheck).where(
        LocationCheck.business_id == current_user.business_id,
        LocationCheck.target_user_id == current_user.id,
        LocationCheck.status.in_(
            [
                LOCATION_CHECK_STATUS_PENDING,
                LOCATION_CHECK_STATUS_SEEN,
            ]
        ),
    )
    count_query = select(func.count(LocationCheck.id)).where(
        LocationCheck.business_id == current_user.business_id,
        LocationCheck.target_user_id == current_user.id,
        LocationCheck.status.in_(
            [
                LOCATION_CHECK_STATUS_PENDING,
                LOCATION_CHECK_STATUS_SEEN,
            ]
        ),
    )

    checks = list(
        db.execute(query.order_by(LocationCheck.created_at_utc.desc()).limit(20))
        .scalars()
        .all()
    )
    total_count = int(db.execute(count_query).scalar_one())

    return LocationCheckListResult(checks=checks, total_count=total_count)


def mark_location_check_seen(
    db: Session,
    *,
    current_user: User,
    location_check_id: int,
) -> LocationCheck:
    """Mark current staff location check as seen."""

    location_check = get_location_check_or_error(db, location_check_id=location_check_id)
    ensure_staff_can_access_location_check(current_user, location_check=location_check)

    if location_check.status == LOCATION_CHECK_STATUS_PENDING:
        now = get_utc_now()
        location_check.status = LOCATION_CHECK_STATUS_SEEN
        location_check.staff_seen_at_utc = now
        location_check.updated_at_utc = now
        db.flush()

    return location_check


def share_location_check(
    db: Session,
    *,
    current_user: User,
    location_check_id: int,
    latitude: float,
    longitude: float,
    location_accuracy: float | None,
    ip_address: str | None,
    user_agent: str | None,
) -> LocationCheck:
    """Store staff location response."""

    location_check = get_location_check_or_error(db, location_check_id=location_check_id)
    ensure_staff_can_access_location_check(current_user, location_check=location_check)

    if location_check.status == LOCATION_CHECK_STATUS_SHARED:
        return location_check

    if location_check.status not in {
        LOCATION_CHECK_STATUS_PENDING,
        LOCATION_CHECK_STATUS_SEEN,
        LOCATION_CHECK_STATUS_FAILED,
        LOCATION_CHECK_STATUS_PERMISSION_DENIED,
    }:
        raise InvalidLocationCheckStateError(
            "Bu konum yoklaması için artık konum paylaşılamaz."
        )

    now = get_utc_now()
    location_check.status = LOCATION_CHECK_STATUS_SHARED
    location_check.latitude = latitude
    location_check.longitude = longitude
    location_check.location_accuracy = location_accuracy
    location_check.response_error_code = None
    location_check.response_error_message = None
    location_check.responded_at_utc = now
    location_check.staff_seen_at_utc = location_check.staff_seen_at_utc or now
    location_check.ip_address = normalize_optional_text(ip_address, max_length=100)
    location_check.user_agent = normalize_optional_text(user_agent, max_length=1000)
    location_check.updated_at_utc = now

    db.flush()
    return location_check


def fail_location_check(
    db: Session,
    *,
    current_user: User,
    location_check_id: int,
    response_error_code: str,
    response_error_message: str | None,
    ip_address: str | None,
    user_agent: str | None,
) -> LocationCheck:
    """Store staff failure response for a location check."""

    location_check = get_location_check_or_error(db, location_check_id=location_check_id)
    ensure_staff_can_access_location_check(current_user, location_check=location_check)

    if location_check.status == LOCATION_CHECK_STATUS_SHARED:
        raise InvalidLocationCheckStateError(
            "Konum paylaşılmış bir yoklama başarısız olarak işaretlenemez."
        )

    now = get_utc_now()
    normalized_error_code = response_error_code.strip().lower()

    if normalized_error_code == "permission_denied":
        location_check.status = LOCATION_CHECK_STATUS_PERMISSION_DENIED
    else:
        location_check.status = LOCATION_CHECK_STATUS_FAILED

    location_check.response_error_code = normalized_error_code[:80]
    location_check.response_error_message = normalize_optional_text(
        response_error_message,
        max_length=1000,
    )
    location_check.responded_at_utc = now
    location_check.staff_seen_at_utc = location_check.staff_seen_at_utc or now
    location_check.ip_address = normalize_optional_text(ip_address, max_length=100)
    location_check.user_agent = normalize_optional_text(user_agent, max_length=1000)
    location_check.updated_at_utc = now

    db.flush()
    return location_check
