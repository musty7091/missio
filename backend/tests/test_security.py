from app.core.roles import can_manage_operations, is_admin_role, is_valid_role
from app.core.security import (
    hash_password,
    is_password_strong,
    validate_password_strength,
    verify_password,
)


def test_password_hash_and_verify() -> None:
    password = "Missio.2026!"
    password_hash = hash_password(password)

    assert password not in password_hash
    assert verify_password(password, password_hash)
    assert not verify_password("Wrong.2026!", password_hash)


def test_password_policy_rejects_weak_password() -> None:
    errors = validate_password_strength("123")

    assert errors


def test_password_policy_accepts_strong_password() -> None:
    assert is_password_strong("Missio.2026!")


def test_role_validation() -> None:
    assert is_valid_role("super_admin")
    assert is_valid_role("staff")
    assert not is_valid_role("unknown_role")


def test_role_permissions() -> None:
    assert is_admin_role("super_admin")
    assert not is_admin_role("staff")
    assert can_manage_operations("manager")
    assert not can_manage_operations("staff")
