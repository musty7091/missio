from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import validate_password_strength
from app.models.app_setting import AppSetting
from app.models.user import User
from app.services.audit_log_service import create_audit_log
from app.services.auth_service import (
    AuthServiceError,
    WeakPasswordError,
    create_user_with_password,
)


class BootstrapError(ValueError):
    """Base error for initial setup bootstrap failures."""


class BootstrapAlreadyCompletedError(BootstrapError):
    """Raised when initial setup was already completed."""


class BootstrapInconsistentStateError(BootstrapError):
    """Raised when setup state and user records are inconsistent."""


@dataclass(frozen=True)
class BootstrapStatus:
    """Initial setup status snapshot."""

    user_count: int
    super_admin_count: int
    setup_completed: bool
    is_ready_for_initial_setup: bool
    is_completed: bool
    is_consistent: bool
    message: str


def get_utc_now() -> datetime:
    """Return current UTC datetime."""

    return datetime.now(timezone.utc)


def get_user_count(db: Session) -> int:
    """Return total user count."""

    statement = select(func.count(User.id))

    return int(db.execute(statement).scalar_one())


def get_super_admin_count(db: Session) -> int:
    """Return active/inactive super admin count."""

    statement = select(func.count(User.id)).where(User.role == "super_admin")

    return int(db.execute(statement).scalar_one())


def get_or_create_app_settings(db: Session) -> AppSetting:
    """Return global app settings row, creating it if missing."""

    app_settings = db.query(AppSetting).first()

    if app_settings is not None:
        return app_settings

    now = get_utc_now()
    app_settings = AppSetting(
        app_name="Missio",
        default_timezone="Europe/Istanbul",
        default_theme="dark",
        setup_completed=False,
        created_at=now,
        updated_at=now,
    )

    db.add(app_settings)
    db.flush()
    db.refresh(app_settings)

    return app_settings


def get_bootstrap_status(db: Session) -> BootstrapStatus:
    """Return initial setup bootstrap status."""

    app_settings = get_or_create_app_settings(db)
    user_count = get_user_count(db)
    super_admin_count = get_super_admin_count(db)
    setup_completed = bool(app_settings.setup_completed)

    if user_count == 0 and not setup_completed:
        return BootstrapStatus(
            user_count=user_count,
            super_admin_count=super_admin_count,
            setup_completed=setup_completed,
            is_ready_for_initial_setup=True,
            is_completed=False,
            is_consistent=True,
            message="İlk kurulum hazır. Henüz kullanıcı oluşturulmamış.",
        )

    if user_count > 0 and setup_completed and super_admin_count > 0:
        return BootstrapStatus(
            user_count=user_count,
            super_admin_count=super_admin_count,
            setup_completed=setup_completed,
            is_ready_for_initial_setup=False,
            is_completed=True,
            is_consistent=True,
            message="İlk kurulum tamamlanmış görünüyor.",
        )

    if user_count > 0 and not setup_completed:
        return BootstrapStatus(
            user_count=user_count,
            super_admin_count=super_admin_count,
            setup_completed=setup_completed,
            is_ready_for_initial_setup=False,
            is_completed=False,
            is_consistent=False,
            message=(
                "Kullanıcı var fakat setup_completed false. "
                "Kurulum durumu tutarsız."
            ),
        )

    if user_count == 0 and setup_completed:
        return BootstrapStatus(
            user_count=user_count,
            super_admin_count=super_admin_count,
            setup_completed=setup_completed,
            is_ready_for_initial_setup=False,
            is_completed=False,
            is_consistent=False,
            message=(
                "setup_completed true fakat kullanıcı yok. "
                "Kurulum durumu tutarsız."
            ),
        )

    return BootstrapStatus(
        user_count=user_count,
        super_admin_count=super_admin_count,
        setup_completed=setup_completed,
        is_ready_for_initial_setup=False,
        is_completed=False,
        is_consistent=False,
        message="Kurulum durumu tutarsız.",
    )


def assert_can_create_initial_super_admin(db: Session) -> None:
    """Validate whether initial super admin can be created."""

    status = get_bootstrap_status(db)

    if not status.is_consistent:
        raise BootstrapInconsistentStateError(status.message)

    if not status.is_ready_for_initial_setup:
        raise BootstrapAlreadyCompletedError("İlk kurulum zaten tamamlanmış.")


def create_initial_super_admin(
    db: Session,
    *,
    full_name: str,
    username: str,
    password: str,
    email: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> User:
    """Create the first installation super admin user."""

    assert_can_create_initial_super_admin(db)

    password_errors = validate_password_strength(password)

    if password_errors:
        raise WeakPasswordError(password_errors)

    try:
        user = create_user_with_password(
            db=db,
            full_name=full_name,
            username=username,
            password=password,
            role="super_admin",
            business_id=None,
            email=email,
            is_active=True,
        )
    except AuthServiceError:
        raise

    app_settings = get_or_create_app_settings(db)
    app_settings.setup_completed = True
    app_settings.updated_at = get_utc_now()
    db.add(app_settings)
    db.flush()

    create_audit_log(
        db=db,
        action="setup.super_admin_created",
        business_id=None,
        user_id=user.id,
        entity_type="user",
        entity_id=str(user.id),
        detail={
            "username": user.username,
            "role": user.role,
            "setup_completed": True,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.flush()
    db.refresh(user)

    return user
