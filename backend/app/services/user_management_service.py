from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.roles import UserRole
from app.models.business import Business
from app.models.user import User
from app.services.access_control_service import ensure_can_create_business_user_role
from app.services.audit_log_service import create_audit_log
from app.services.auth_service import create_user_with_password
from app.services.subscription_service import (
    BusinessSubscriptionNotFoundError,
    BusinessUserLimitExceededError,
    ensure_business_active_user_limit_available,
)


class BusinessUserManagementError(ValueError):
    """Base error for business user management failures."""


class InvalidBusinessUserRoleError(BusinessUserManagementError):
    """Raised when a business user role is invalid."""


class InvalidBusinessUserSupervisorError(BusinessUserManagementError):
    """Raised when a business user supervisor is invalid."""


ALLOWED_BUSINESS_USER_ROLES = {
    UserRole.BOSS.value,
    UserRole.MANAGER.value,
    UserRole.STAFF.value,
}


@dataclass(frozen=True)
class CreatedBusinessUser:
    """Created business user result."""

    user: User
    business: Business


def get_utc_now() -> datetime:
    """Return current UTC datetime."""

    return datetime.now(timezone.utc)


def validate_business_user_role(role: str) -> None:
    """Validate business user role."""

    if role not in ALLOWED_BUSINESS_USER_ROLES:
        raise InvalidBusinessUserRoleError("İşletme kullanıcısı rolü geçersiz.")


def resolve_business_user_supervisor(
    db: Session,
    *,
    business: Business,
    target_role: str,
    supervisor_user_id: int | None,
) -> User | None:
    """Return valid supervisor for a staff user or None.

    The supervisor field is intentionally nullable for the first rollout so that
    existing staff users can be assigned later from the personnel management page.
    """

    if target_role != UserRole.STAFF.value:
        if supervisor_user_id is not None:
            raise InvalidBusinessUserSupervisorError(
                "Sorumlu yönetici sadece personel kullanıcılar için seçilebilir."
            )

        return None

    if supervisor_user_id is None:
        return None

    supervisor_user = db.get(User, supervisor_user_id)

    if supervisor_user is None:
        raise InvalidBusinessUserSupervisorError("Sorumlu yönetici bulunamadı.")

    if supervisor_user.business_id != business.id:
        raise InvalidBusinessUserSupervisorError(
            "Sorumlu yönetici ilgili işletmeye ait değil."
        )

    if supervisor_user.role != UserRole.MANAGER.value:
        raise InvalidBusinessUserSupervisorError(
            "Sorumlu kullanıcı manager rolünde olmalıdır."
        )

    if not supervisor_user.is_active:
        raise InvalidBusinessUserSupervisorError(
            "Pasif manager sorumlu yönetici olarak seçilemez."
        )

    return supervisor_user


def ensure_business_can_add_active_user(
    db: Session,
    *,
    business: Business,
) -> None:
    """Ensure business subscription allows creating one more active user."""

    try:
        ensure_business_active_user_limit_available(
            db=db,
            business_id=business.id,
            extra_user_count=1,
        )
    except BusinessSubscriptionNotFoundError as exc:
        raise BusinessUserManagementError(
            "İşletmenin aktif aboneliği bulunamadığı için kullanıcı oluşturulamaz."
        ) from exc
    except BusinessUserLimitExceededError as exc:
        raise BusinessUserManagementError(
            "İşletmenin aktif kullanıcı limiti dolmuştur."
        ) from exc


def create_business_user(
    db: Session,
    *,
    current_user: User,
    business: Business,
    full_name: str,
    username: str,
    password: str,
    role: str,
    email: str | None = None,
    theme_preference: str | None = None,
    supervisor_user_id: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> User:
    """Create a business scoped user according to the role permission matrix."""

    validate_business_user_role(role)

    if not business.is_active:
        raise BusinessUserManagementError("Pasif işletmeye kullanıcı oluşturulamaz.")

    ensure_can_create_business_user_role(
        current_user,
        target_business_id=business.id,
        target_role=role,
    )

    ensure_business_can_add_active_user(
        db=db,
        business=business,
    )

    supervisor_user = resolve_business_user_supervisor(
        db=db,
        business=business,
        target_role=role,
        supervisor_user_id=supervisor_user_id,
    )

    user = create_user_with_password(
        db=db,
        full_name=full_name,
        username=username,
        password=password,
        role=role,
        business_id=business.id,
        email=email,
        theme_preference=theme_preference,
        is_active=True,
    )

    user.supervisor_user_id = supervisor_user.id if supervisor_user is not None else None
    db.add(user)
    db.flush()

    create_audit_log(
        db=db,
        action="business.user_created",
        business_id=business.id,
        user_id=current_user.id,
        entity_type="user",
        entity_id=str(user.id),
        detail={
            "business_id": business.id,
            "created_user_id": user.id,
            "username": user.username,
            "role": user.role,
            "supervisor_user_id": user.supervisor_user_id,
            "created_by_user_id": current_user.id,
            "created_by_role": current_user.role,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return user