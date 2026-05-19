from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    """Supported Missio user roles."""

    SUPER_ADMIN = "super_admin"
    BOSS = "boss"
    MANAGER = "manager"
    BUSINESS_OWNER = "business_owner"
    STAFF = "staff"


ADMIN_ROLES: set[UserRole] = {
    UserRole.SUPER_ADMIN,
    UserRole.BOSS,
}

OPERATION_MANAGER_ROLES: set[UserRole] = {
    UserRole.SUPER_ADMIN,
    UserRole.BOSS,
    UserRole.MANAGER,
}

STAFF_VISIBLE_ROLES: set[UserRole] = {
    UserRole.STAFF,
}

ROLE_LABELS: dict[UserRole, str] = {
    UserRole.SUPER_ADMIN: "Süper Admin",
    UserRole.BOSS: "Patron",
    UserRole.MANAGER: "Yönetici",
    UserRole.BUSINESS_OWNER: "İşletme Sahibi",
    UserRole.STAFF: "Personel",
}


def get_all_role_values() -> list[str]:
    """Return all role values as strings."""

    return [role.value for role in UserRole]


def is_valid_role(role: str) -> bool:
    """Return whether the given role is supported."""

    return role in get_all_role_values()


def is_admin_role(role: str) -> bool:
    """Return whether the given role has admin level privileges."""

    if not is_valid_role(role):
        return False

    return UserRole(role) in ADMIN_ROLES


def can_manage_operations(role: str) -> bool:
    """Return whether the given role can manage operational tasks."""

    if not is_valid_role(role):
        return False

    return UserRole(role) in OPERATION_MANAGER_ROLES


def get_role_label(role: str) -> str:
    """Return Turkish display label for the given role."""

    if not is_valid_role(role):
        return "Bilinmeyen Rol"

    return ROLE_LABELS[UserRole(role)]
