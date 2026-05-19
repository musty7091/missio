from __future__ import annotations

from collections.abc import Iterable

from app.core.roles import OPERATION_MANAGER_ROLES, UserRole, is_valid_role
from app.models.user import User


class AccessControlError(PermissionError):
    """Base error for access control failures."""


class RolePermissionError(AccessControlError):
    """Raised when user role is not allowed for an operation."""


class BusinessScopeError(AccessControlError):
    """Raised when user tries to access another business scope."""


class UserRecordAccessError(AccessControlError):
    """Raised when user tries to access a forbidden user record."""


def normalize_allowed_roles(allowed_roles: Iterable[str | UserRole]) -> set[str]:
    """Normalize allowed roles to string values."""

    normalized_roles: set[str] = set()

    for role in allowed_roles:
        role_value = role.value if isinstance(role, UserRole) else str(role)

        if not is_valid_role(role_value):
            raise ValueError(f"Geçersiz rol: {role_value}")

        normalized_roles.add(role_value)

    if not normalized_roles:
        raise ValueError("En az bir rol belirtilmelidir.")

    return normalized_roles


def is_super_admin(user: User) -> bool:
    """Return whether the user is a super admin."""

    return user.role == UserRole.SUPER_ADMIN.value


def require_roles(user: User, allowed_roles: Iterable[str | UserRole]) -> None:
    """Raise if user role is not in allowed roles."""

    normalized_roles = normalize_allowed_roles(allowed_roles)

    if user.role not in normalized_roles:
        raise RolePermissionError("Bu işlem için yetkiniz yok.")


def require_operation_manager_role(user: User) -> None:
    """Raise if user cannot manage operational records."""

    require_roles(user, OPERATION_MANAGER_ROLES)


def ensure_business_scope(
    user: User,
    target_business_id: int | None,
    *,
    allow_super_admin: bool = True,
) -> None:
    """Ensure user can access the target business scope."""

    if allow_super_admin and is_super_admin(user):
        return

    if target_business_id is None:
        raise BusinessScopeError("İşletme kapsamı gerekli.")

    if user.business_id is None:
        raise BusinessScopeError("Kullanıcının işletme kapsamı yok.")

    if user.business_id != target_business_id:
        raise BusinessScopeError("Bu işletme verisine erişim yetkiniz yok.")


def ensure_user_record_access(
    current_user: User,
    target_user: User,
    *,
    allow_super_admin: bool = True,
) -> None:
    """Ensure current user can access target user record."""

    if allow_super_admin and is_super_admin(current_user):
        return

    ensure_business_scope(
        current_user,
        target_user.business_id,
        allow_super_admin=allow_super_admin,
    )

    if current_user.role == UserRole.STAFF.value and current_user.id != target_user.id:
        raise UserRecordAccessError("Personel sadece kendi kaydını görebilir.")


def ensure_staff_task_access(
    current_user: User,
    *,
    task_business_id: int,
    assigned_to_user_id: int | None,
) -> None:
    """Ensure staff users can only access their own assigned tasks."""

    ensure_business_scope(current_user, task_business_id)

    if current_user.role != UserRole.STAFF.value:
        return

    if assigned_to_user_id != current_user.id:
        raise UserRecordAccessError("Personel sadece kendi görevlerini görebilir.")
