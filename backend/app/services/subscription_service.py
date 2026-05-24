from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.roles import UserRole
from app.models.business import Business
from app.models.business_subscription import BusinessSubscription
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.services.access_control_service import require_roles
from app.services.audit_log_service import create_audit_log


class SubscriptionServiceError(ValueError):
    """Base error for subscription service failures."""


class SubscriptionPlanNotFoundError(SubscriptionServiceError):
    """Raised when subscription plan cannot be found."""


class BusinessNotFoundForSubscriptionError(SubscriptionServiceError):
    """Raised when target business cannot be found."""


class BusinessSubscriptionNotFoundError(SubscriptionServiceError):
    """Raised when current business subscription cannot be found."""


class BusinessSubscriptionInactiveError(SubscriptionServiceError):
    """Raised when current business subscription is not usable."""


class BusinessSubscriptionExpiredError(SubscriptionServiceError):
    """Raised when current business subscription is expired."""


class BusinessUserLimitExceededError(SubscriptionServiceError):
    """Raised when business active user limit would be exceeded."""


class BusinessSubscriptionCannotBeExtendedError(SubscriptionServiceError):
    """Raised when current subscription cannot be extended safely."""


class BusinessSubscriptionStatusUpdateError(SubscriptionServiceError):
    """Raised when subscription status cannot be updated safely."""


class SubscriptionPlanUserLimitTooLowError(SubscriptionServiceError):
    """Raised when selected plan cannot cover current active users."""


ACTIVE_SUBSCRIPTION_STATUSES = {
    "trialing",
    "active",
}

VALID_SUBSCRIPTION_STATUSES = {
    "trialing",
    "active",
    "suspended",
    "cancelled",
    "expired",
}

VALID_BILLING_PERIODS = {
    "manual",
    "trial",
    "monthly",
    "yearly",
    "custom",
}

VALID_SUBSCRIPTION_CHANGE_MODES = {
    "replace",
    "extend",
}


def get_utc_now() -> datetime:
    """Return current UTC datetime."""

    return datetime.now(timezone.utc)


def _as_utc_aware(value: datetime | None) -> datetime | None:
    """Normalize datetime values for safe comparisons."""

    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _normalize_plan_code(plan_code: str) -> str:
    """Normalize subscription plan code."""

    normalized = plan_code.strip().lower()

    if not normalized:
        raise SubscriptionServiceError("Abonelik plan kodu boş olamaz.")

    return normalized


def _validate_subscription_status(status: str) -> str:
    """Validate subscription status."""

    normalized = status.strip().lower()

    if normalized not in VALID_SUBSCRIPTION_STATUSES:
        raise SubscriptionServiceError("Abonelik durumu geçersiz.")

    return normalized


def _validate_billing_period(billing_period: str) -> str:
    """Validate billing period."""

    normalized = billing_period.strip().lower()

    if normalized not in VALID_BILLING_PERIODS:
        raise SubscriptionServiceError("Abonelik ödeme periyodu geçersiz.")

    return normalized


def _validate_subscription_change_mode(change_mode: str) -> str:
    """Validate subscription change mode."""

    normalized = change_mode.strip().lower()

    if normalized not in VALID_SUBSCRIPTION_CHANGE_MODES:
        raise SubscriptionServiceError("Abonelik güncelleme türü geçersiz.")

    return normalized


def list_active_subscription_plans(db: Session) -> list[SubscriptionPlan]:
    """Return active subscription plans ordered for display."""

    return (
        db.query(SubscriptionPlan)
        .filter(SubscriptionPlan.is_active.is_(True))
        .order_by(SubscriptionPlan.display_order.asc(), SubscriptionPlan.id.asc())
        .all()
    )


def get_subscription_plan_by_code(
    db: Session,
    *,
    plan_code: str,
    active_only: bool = True,
) -> SubscriptionPlan | None:
    """Return subscription plan by code."""

    normalized_code = _normalize_plan_code(plan_code)

    query = db.query(SubscriptionPlan).filter(SubscriptionPlan.code == normalized_code)

    if active_only:
        query = query.filter(SubscriptionPlan.is_active.is_(True))

    return query.one_or_none()


def require_subscription_plan_by_code(
    db: Session,
    *,
    plan_code: str,
    active_only: bool = True,
) -> SubscriptionPlan:
    """Return subscription plan or raise a controlled service error."""

    plan = get_subscription_plan_by_code(
        db=db,
        plan_code=plan_code,
        active_only=active_only,
    )

    if plan is None:
        raise SubscriptionPlanNotFoundError("Abonelik planı bulunamadı.")

    return plan


def get_current_business_subscription(
    db: Session,
    *,
    business_id: int,
) -> BusinessSubscription | None:
    """Return current subscription for a business."""

    return (
        db.query(BusinessSubscription)
        .filter(
            BusinessSubscription.business_id == business_id,
            BusinessSubscription.is_current.is_(True),
        )
        .order_by(BusinessSubscription.id.desc())
        .first()
    )


def require_current_business_subscription(
    db: Session,
    *,
    business_id: int,
) -> BusinessSubscription:
    """Return current business subscription or raise error."""

    subscription = get_current_business_subscription(
        db=db,
        business_id=business_id,
    )

    if subscription is None:
        raise BusinessSubscriptionNotFoundError("İşletme aboneliği bulunamadı.")

    return subscription


def count_active_business_users(
    db: Session,
    *,
    business_id: int,
) -> int:
    """Count active users for a business."""

    count = (
        db.query(func.count(User.id))
        .filter(
            User.business_id == business_id,
            User.is_active.is_(True),
        )
        .scalar()
    )

    return int(count or 0)


def ensure_business_subscription_is_usable_for_login(
    db: Session,
    *,
    business_id: int | None,
) -> BusinessSubscription | None:
    """
    Validate tenant subscription before login.

    Super admin users can have no business_id, so they do not need a tenant subscription.
    """

    if business_id is None:
        return None

    subscription = require_current_business_subscription(
        db=db,
        business_id=business_id,
    )

    if subscription.status not in ACTIVE_SUBSCRIPTION_STATUSES:
        raise BusinessSubscriptionInactiveError("İşletme aboneliği aktif değil.")

    now = get_utc_now()
    ends_at_utc = _as_utc_aware(subscription.ends_at_utc)

    if ends_at_utc is not None and ends_at_utc < now:
        raise BusinessSubscriptionExpiredError("İşletme aboneliği sona ermiş.")

    return subscription


def ensure_business_active_user_limit_available(
    db: Session,
    *,
    business_id: int,
    extra_user_count: int = 1,
) -> BusinessSubscription:
    """Ensure business active user limit allows adding new active users."""

    if extra_user_count < 1:
        raise SubscriptionServiceError("Eklenecek kullanıcı sayısı geçersiz.")

    subscription = require_current_business_subscription(
        db=db,
        business_id=business_id,
    )

    active_user_count = count_active_business_users(
        db=db,
        business_id=business_id,
    )

    if active_user_count + extra_user_count > subscription.max_users_snapshot:
        raise BusinessUserLimitExceededError(
            "İşletmenin aktif kullanıcı limiti dolmuştur."
        )

    return subscription


def deactivate_current_business_subscriptions(
    db: Session,
    *,
    business_id: int,
) -> int:
    """Mark existing current subscriptions as historical."""

    subscriptions = (
        db.query(BusinessSubscription)
        .filter(
            BusinessSubscription.business_id == business_id,
            BusinessSubscription.is_current.is_(True),
        )
        .all()
    )

    now = get_utc_now()

    for subscription in subscriptions:
        subscription.is_current = False
        subscription.updated_at_utc = now

    if subscriptions:
        db.flush()

    return len(subscriptions)


def create_business_subscription(
    db: Session,
    *,
    current_user: User,
    business_id: int,
    plan_code: str,
    starts_at_utc: datetime | None = None,
    ends_at_utc: datetime | None = None,
    status: str = "trialing",
    billing_period: str = "manual",
    notes: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> BusinessSubscription:
    """Create a current subscription for a business as super admin."""

    require_roles(current_user, [UserRole.SUPER_ADMIN])

    business = db.query(Business).filter(Business.id == business_id).one_or_none()

    if business is None:
        raise BusinessNotFoundForSubscriptionError("İşletme bulunamadı.")

    plan = require_subscription_plan_by_code(
        db=db,
        plan_code=plan_code,
        active_only=True,
    )

    normalized_status = _validate_subscription_status(status)
    normalized_billing_period = _validate_billing_period(billing_period)

    now = get_utc_now()
    normalized_starts_at_utc = _as_utc_aware(starts_at_utc) or now
    normalized_ends_at_utc = _as_utc_aware(ends_at_utc)

    deactivate_current_business_subscriptions(
        db=db,
        business_id=business.id,
    )

    subscription = BusinessSubscription(
        business_id=business.id,
        plan_id=plan.id,
        status=normalized_status,
        billing_period=normalized_billing_period,
        starts_at_utc=normalized_starts_at_utc,
        ends_at_utc=normalized_ends_at_utc,
        activated_at_utc=now if normalized_status == "active" else None,
        suspended_at_utc=now if normalized_status == "suspended" else None,
        cancelled_at_utc=now if normalized_status == "cancelled" else None,
        is_current=True,
        max_users_snapshot=plan.max_users,
        max_managers_snapshot=plan.max_managers,
        max_daily_tasks_snapshot=plan.max_daily_tasks,
        report_retention_days_snapshot=plan.report_retention_days,
        price_monthly_snapshot=plan.price_monthly,
        price_yearly_snapshot=plan.price_yearly,
        currency_snapshot=plan.currency,
        notes=notes.strip() if notes else None,
        created_by_user_id=current_user.id,
        created_at_utc=now,
        updated_at_utc=now,
    )

    db.add(subscription)
    db.flush()
    db.refresh(subscription)

    create_audit_log(
        db=db,
        action="business_subscription.created",
        business_id=business.id,
        user_id=current_user.id,
        entity_type="business_subscription",
        entity_id=str(subscription.id),
        detail={
            "business_id": business.id,
            "subscription_id": subscription.id,
            "plan_id": plan.id,
            "plan_code": plan.code,
            "status": subscription.status,
            "billing_period": subscription.billing_period,
            "starts_at_utc": subscription.starts_at_utc,
            "ends_at_utc": subscription.ends_at_utc,
            "max_users_snapshot": subscription.max_users_snapshot,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return subscription


def create_trial_subscription_for_business(
    db: Session,
    *,
    current_user: User,
    business_id: int,
    trial_days: int = 14,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> BusinessSubscription:
    """Create default trial subscription for a business."""

    if trial_days < 1:
        raise SubscriptionServiceError("Deneme süresi en az 1 gün olmalıdır.")

    starts_at_utc = get_utc_now()
    ends_at_utc = starts_at_utc + timedelta(days=trial_days)

    return create_business_subscription(
        db=db,
        current_user=current_user,
        business_id=business_id,
        plan_code="trial",
        starts_at_utc=starts_at_utc,
        ends_at_utc=ends_at_utc,
        status="trialing",
        billing_period="trial",
        notes=f"{trial_days} günlük deneme aboneliği.",
        ip_address=ip_address,
        user_agent=user_agent,
    )


def change_business_subscription_plan(
    db: Session,
    *,
    current_user: User,
    business_id: int,
    plan_code: str,
    duration_days: int,
    billing_period: str = "manual",
    status: str = "active",
    change_mode: str = "extend",
    notes: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> BusinessSubscription:
    """
    Change current business subscription plan as super admin.

    replace:
        New plan starts now and ends after duration_days.

    extend:
        New plan becomes active immediately, but if the business still has
        a future subscription end date, duration_days is added to that date.
    """

    require_roles(current_user, [UserRole.SUPER_ADMIN])

    if duration_days < 1:
        raise SubscriptionServiceError("Abonelik süresi en az 1 gün olmalıdır.")

    if duration_days > 3650:
        raise SubscriptionServiceError("Abonelik süresi en fazla 3650 gün olabilir.")

    business = db.query(Business).filter(Business.id == business_id).one_or_none()

    if business is None:
        raise BusinessNotFoundForSubscriptionError("İşletme bulunamadı.")

    plan = require_subscription_plan_by_code(
        db=db,
        plan_code=plan_code,
        active_only=True,
    )

    active_user_count = count_active_business_users(
        db=db,
        business_id=business.id,
    )

    if active_user_count > plan.max_users:
        raise SubscriptionPlanUserLimitTooLowError(
            "Seçilen plan işletmenin mevcut aktif kullanıcı sayısını karşılamıyor."
        )

    normalized_status = _validate_subscription_status(status)
    normalized_billing_period = _validate_billing_period(billing_period)
    normalized_change_mode = _validate_subscription_change_mode(change_mode)

    now = get_utc_now()
    current_subscription = get_current_business_subscription(
        db=db,
        business_id=business.id,
    )

    current_ends_at_utc = (
        _as_utc_aware(current_subscription.ends_at_utc)
        if current_subscription is not None
        else None
    )

    starts_at_utc = now

    if (
        normalized_change_mode == "extend"
        and current_ends_at_utc is not None
        and current_ends_at_utc > now
    ):
        ends_at_utc = current_ends_at_utc + timedelta(days=duration_days)
    else:
        ends_at_utc = now + timedelta(days=duration_days)

    normalized_notes = notes.strip() if notes else None

    if normalized_notes:
        final_notes = normalized_notes
    else:
        final_notes = (
            f"Plan değişikliği: {plan.code} | "
            f"Güncelleme türü: {normalized_change_mode} | "
            f"Süre: {duration_days} gün | "
            f"Aktif kullanıcı: {active_user_count}"
        )

    subscription = create_business_subscription(
        db=db,
        current_user=current_user,
        business_id=business.id,
        plan_code=plan.code,
        starts_at_utc=starts_at_utc,
        ends_at_utc=ends_at_utc,
        status=normalized_status,
        billing_period=normalized_billing_period,
        notes=final_notes,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    create_audit_log(
        db=db,
        action="business_subscription.plan_changed",
        business_id=business.id,
        user_id=current_user.id,
        entity_type="business_subscription",
        entity_id=str(subscription.id),
        detail={
            "business_id": business.id,
            "subscription_id": subscription.id,
            "plan_id": plan.id,
            "plan_code": plan.code,
            "duration_days": duration_days,
            "change_mode": normalized_change_mode,
            "billing_period": subscription.billing_period,
            "status": subscription.status,
            "active_user_count": active_user_count,
            "previous_subscription_id": (
                current_subscription.id if current_subscription is not None else None
            ),
            "previous_ends_at_utc": current_ends_at_utc,
            "max_users_snapshot": subscription.max_users_snapshot,
            "starts_at_utc": subscription.starts_at_utc,
            "ends_at_utc": subscription.ends_at_utc,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return subscription

def extend_business_subscription(
    db: Session,
    *,
    current_user: User,
    business_id: int,
    duration_days: int,
    billing_period: str = "monthly",
    notes: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> BusinessSubscription:
    """
    Extend current business subscription without changing its plan.

    If current subscription has a future end date, duration_days is added to it.
    If current subscription is already expired by date, duration starts from now.
    """

    require_roles(current_user, [UserRole.SUPER_ADMIN])

    if duration_days < 1:
        raise SubscriptionServiceError("Abonelik süresi en az 1 gün olmalıdır.")

    if duration_days > 3650:
        raise SubscriptionServiceError("Abonelik süresi en fazla 3650 gün olabilir.")

    business = db.query(Business).filter(Business.id == business_id).one_or_none()

    if business is None:
        raise BusinessNotFoundForSubscriptionError("İşletme bulunamadı.")

    current_subscription = require_current_business_subscription(
        db=db,
        business_id=business.id,
    )

    if current_subscription.status in {"suspended", "cancelled"}:
        raise BusinessSubscriptionCannotBeExtendedError(
            "Askıda veya iptal edilmiş abonelik süre uzatma ile güncellenemez."
        )

    plan = (
        db.query(SubscriptionPlan)
        .filter(SubscriptionPlan.id == current_subscription.plan_id)
        .one_or_none()
    )

    if plan is None:
        raise SubscriptionPlanNotFoundError("Abonelik planı bulunamadı.")

    normalized_billing_period = _validate_billing_period(billing_period)

    now = get_utc_now()
    current_ends_at_utc = _as_utc_aware(current_subscription.ends_at_utc)

    if current_ends_at_utc is not None and current_ends_at_utc > now:
        base_ends_at_utc = current_ends_at_utc
    else:
        base_ends_at_utc = now

    new_ends_at_utc = base_ends_at_utc + timedelta(days=duration_days)

    normalized_notes = notes.strip() if notes else None

    if normalized_notes:
        final_notes = normalized_notes
    else:
        final_notes = (
            f"Süre uzatma: {duration_days} gün | "
            f"Plan: {plan.code} | "
            f"Başlangıç referansı: {base_ends_at_utc.isoformat()}"
        )

    subscription = create_business_subscription(
        db=db,
        current_user=current_user,
        business_id=business.id,
        plan_code=plan.code,
        starts_at_utc=now,
        ends_at_utc=new_ends_at_utc,
        status="active",
        billing_period=normalized_billing_period,
        notes=final_notes,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    create_audit_log(
        db=db,
        action="business_subscription.extended",
        business_id=business.id,
        user_id=current_user.id,
        entity_type="business_subscription",
        entity_id=str(subscription.id),
        detail={
            "business_id": business.id,
            "previous_subscription_id": current_subscription.id,
            "new_subscription_id": subscription.id,
            "plan_id": plan.id,
            "plan_code": plan.code,
            "duration_days": duration_days,
            "billing_period": subscription.billing_period,
            "previous_ends_at_utc": current_ends_at_utc,
            "base_ends_at_utc": base_ends_at_utc,
            "new_ends_at_utc": subscription.ends_at_utc,
            "max_users_snapshot": subscription.max_users_snapshot,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return subscription

def change_business_plan(
    db: Session,
    *,
    current_user: User,
    business_id: int,
    plan_code: str,
    preserve_remaining_time: bool = True,
    notes: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> BusinessSubscription:
    """
    Change business plan without extending subscription duration.

    New plan becomes active immediately.
    If preserve_remaining_time is true, current subscription end date is preserved.
    If current subscription has no future end date, the new subscription starts from now
    and keeps the previous end date as-is if available.
    """

    require_roles(current_user, [UserRole.SUPER_ADMIN])

    business = db.query(Business).filter(Business.id == business_id).one_or_none()

    if business is None:
        raise BusinessNotFoundForSubscriptionError("İşletme bulunamadı.")

    current_subscription = require_current_business_subscription(
        db=db,
        business_id=business.id,
    )

    if current_subscription.status in {"suspended", "cancelled"}:
        raise BusinessSubscriptionCannotBeExtendedError(
            "Askıda veya iptal edilmiş abonelikte plan değişikliği yapılamaz."
        )

    target_plan = require_subscription_plan_by_code(
        db=db,
        plan_code=plan_code,
        active_only=True,
    )

    active_user_count = count_active_business_users(
        db=db,
        business_id=business.id,
    )

    if active_user_count > target_plan.max_users:
        raise SubscriptionPlanUserLimitTooLowError(
            "Seçilen plan işletmenin mevcut aktif kullanıcı sayısını karşılamıyor."
        )

    now = get_utc_now()
    current_ends_at_utc = _as_utc_aware(current_subscription.ends_at_utc)

    if preserve_remaining_time:
        new_ends_at_utc = current_ends_at_utc
    else:
        new_ends_at_utc = now + timedelta(days=30)

    normalized_notes = notes.strip() if notes else None

    if normalized_notes:
        final_notes = normalized_notes
    else:
        final_notes = (
            f"Plan değişikliği: {target_plan.code} | "
            f"Kalan süre korundu: {preserve_remaining_time} | "
            f"Aktif kullanıcı: {active_user_count}"
        )

    subscription = create_business_subscription(
        db=db,
        current_user=current_user,
        business_id=business.id,
        plan_code=target_plan.code,
        starts_at_utc=now,
        ends_at_utc=new_ends_at_utc,
        status="active",
        billing_period=current_subscription.billing_period,
        notes=final_notes,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    create_audit_log(
        db=db,
        action="business_subscription.plan_changed_only",
        business_id=business.id,
        user_id=current_user.id,
        entity_type="business_subscription",
        entity_id=str(subscription.id),
        detail={
            "business_id": business.id,
            "previous_subscription_id": current_subscription.id,
            "new_subscription_id": subscription.id,
            "previous_plan_id": current_subscription.plan_id,
            "target_plan_id": target_plan.id,
            "target_plan_code": target_plan.code,
            "active_user_count": active_user_count,
            "preserve_remaining_time": preserve_remaining_time,
            "previous_ends_at_utc": current_ends_at_utc,
            "new_ends_at_utc": subscription.ends_at_utc,
            "max_users_snapshot": subscription.max_users_snapshot,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return subscription

def update_business_subscription_status(
    db: Session,
    *,
    current_user: User,
    business_id: int,
    status: str,
    notes: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> BusinessSubscription:
    """Update current business subscription status without changing plan or end date."""

    require_roles(current_user, [UserRole.SUPER_ADMIN])

    business = db.query(Business).filter(Business.id == business_id).one_or_none()

    if business is None:
        raise BusinessNotFoundForSubscriptionError("İşletme bulunamadı.")

    normalized_status = _validate_subscription_status(status)

    if normalized_status not in {"active", "suspended", "cancelled"}:
        raise BusinessSubscriptionStatusUpdateError(
            "Bu işlem için yalnız aktif, askıda veya iptal durumu kullanılabilir."
        )

    current_subscription = require_current_business_subscription(
        db=db,
        business_id=business.id,
    )

    if current_subscription.status == normalized_status:
        return current_subscription

    plan = (
        db.query(SubscriptionPlan)
        .filter(SubscriptionPlan.id == current_subscription.plan_id)
        .one_or_none()
    )

    if plan is None:
        raise SubscriptionPlanNotFoundError("Abonelik planı bulunamadı.")

    now = get_utc_now()
    current_ends_at_utc = _as_utc_aware(current_subscription.ends_at_utc)

    if (
        normalized_status == "active"
        and current_ends_at_utc is not None
        and current_ends_at_utc < now
    ):
        raise BusinessSubscriptionStatusUpdateError(
            "Süresi dolmuş abonelik doğrudan aktif edilemez. Önce süre uzatın."
        )

    normalized_notes = notes.strip() if notes else None

    if normalized_notes:
        final_notes = normalized_notes
    else:
        final_notes = (
            f"Abonelik durum değişikliği: "
            f"{current_subscription.status} -> {normalized_status}"
        )

    subscription = create_business_subscription(
        db=db,
        current_user=current_user,
        business_id=business.id,
        plan_code=plan.code,
        starts_at_utc=now,
        ends_at_utc=current_subscription.ends_at_utc,
        status=normalized_status,
        billing_period=current_subscription.billing_period,
        notes=final_notes,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    create_audit_log(
        db=db,
        action="business_subscription.status_updated",
        business_id=business.id,
        user_id=current_user.id,
        entity_type="business_subscription",
        entity_id=str(subscription.id),
        detail={
            "business_id": business.id,
            "previous_subscription_id": current_subscription.id,
            "new_subscription_id": subscription.id,
            "plan_id": plan.id,
            "plan_code": plan.code,
            "previous_status": current_subscription.status,
            "new_status": subscription.status,
            "ends_at_utc": subscription.ends_at_utc,
            "max_users_snapshot": subscription.max_users_snapshot,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return subscription

