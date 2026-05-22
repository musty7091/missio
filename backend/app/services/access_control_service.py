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


class BusinessUserManagementPermissionError(AccessControlError):
    """Raised when user cannot manage a business user role."""


BOSS_LEVEL_ROLES: set[UserRole] = {
    UserRole.BOSS,
}

BUSINESS_ADMIN_ROLES: set[UserRole] = {
    UserRole.SUPER_ADMIN,
    UserRole.BOSS,
}

BUSINESS_USER_MANAGER_ROLES: set[UserRole] = {
    UserRole.SUPER_ADMIN,
    UserRole.BOSS,
    UserRole.MANAGER,
}

BUSINESS_USER_ROLES: set[UserRole] = {
    UserRole.BOSS,
    UserRole.MANAGER,
    UserRole.STAFF,
}


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


def normalize_role_value(role: str | UserRole) -> str:
    """Normalize and validate a single role value."""

    role_value = role.value if isinstance(role, UserRole) else str(role)

    if not is_valid_role(role_value):
        raise ValueError(f"Geçersiz rol: {role_value}")

    return role_value


def user_has_role(user: User, role: str | UserRole) -> bool:
    """Return whether user has the given role."""

    return user.role == normalize_role_value(role)


def user_has_any_role(user: User, roles: Iterable[str | UserRole]) -> bool:
    """Return whether user has any of the given roles."""

    return user.role in normalize_allowed_roles(roles)


def is_super_admin(user: User) -> bool:
    """Return whether the user is a super admin."""

    return user.role == UserRole.SUPER_ADMIN.value


def is_boss_level_user(user: User) -> bool:
    """Return whether user has boss-level business authority."""

    return user_has_any_role(user, BOSS_LEVEL_ROLES)


def is_manager_user(user: User) -> bool:
    """Return whether user is a manager."""

    return user.role == UserRole.MANAGER.value


def is_staff_user(user: User) -> bool:
    """Return whether user is a staff user."""

    return user.role == UserRole.STAFF.value


def require_roles(user: User, allowed_roles: Iterable[str | UserRole]) -> None:
    """Raise if user role is not in allowed roles."""

    normalized_roles = normalize_allowed_roles(allowed_roles)

    if user.role not in normalized_roles:
        raise RolePermissionError("Bu işlem için yetkiniz yok.")


def require_operation_manager_role(user: User) -> None:
    """Raise if user cannot manage operational records."""

    require_roles(user, OPERATION_MANAGER_ROLES)


def require_business_admin_role(user: User) -> None:
    """Raise if user cannot manage business-level settings."""

    require_roles(user, BUSINESS_ADMIN_ROLES)


def require_business_user_manager_role(user: User) -> None:
    """Raise if user cannot manage business users."""

    require_roles(user, BUSINESS_USER_MANAGER_ROLES)


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


def ensure_business_admin_access(
    current_user: User,
    target_business_id: int | None,
    *,
    allow_super_admin: bool = True,
) -> None:
    """Ensure current user can manage business-level settings."""

    ensure_business_scope(
        current_user,
        target_business_id,
        allow_super_admin=allow_super_admin,
    )
    require_business_admin_role(current_user)


def ensure_business_user_management_access(
    current_user: User,
    target_business_id: int | None,
    *,
    allow_super_admin: bool = True,
) -> None:
    """Ensure current user can manage users within a business."""

    ensure_business_scope(
        current_user,
        target_business_id,
        allow_super_admin=allow_super_admin,
    )
    require_business_user_manager_role(current_user)


def ensure_can_create_business_user_role(
    current_user: User,
    *,
    target_business_id: int | None,
    target_role: str | UserRole,
    allow_super_admin: bool = True,
) -> None:
    """Ensure current user can create a user with the target business role."""

    target_role_value = normalize_role_value(target_role)

    if target_role_value == UserRole.SUPER_ADMIN.value:
        raise BusinessUserManagementPermissionError(
            "İşletme kullanıcısı olarak super_admin oluşturulamaz."
        )

    if UserRole(target_role_value) not in BUSINESS_USER_ROLES:
        raise BusinessUserManagementPermissionError(
            "İşletme kullanıcısı rolü geçersiz."
        )

    ensure_business_scope(
        current_user,
        target_business_id,
        allow_super_admin=allow_super_admin,
    )

    if is_super_admin(current_user):
        return

    if is_boss_level_user(current_user):
        if target_role_value in {
            UserRole.MANAGER.value,
            UserRole.STAFF.value,
        }:
            return

        raise BusinessUserManagementPermissionError(
            "Patron sadece manager veya personel kullanıcısı oluşturabilir."
        )

    if is_manager_user(current_user):
        if target_role_value == UserRole.STAFF.value:
            return

        raise BusinessUserManagementPermissionError(
            "Manager sadece personel kullanıcısı oluşturabilir."
        )

    raise BusinessUserManagementPermissionError(
        "Bu kullanıcı işletme kullanıcısı oluşturamaz."
    )


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
